"""Build CycloneDX 1.6 or SPDX 3.0 AI Bill of Materials from a :class:`ScanResult`.

CycloneDX is the default and primary format (auditor-grade, validated schema).
SPDX 3.0 with AI Profile is available via build_spdx() for SPDX-native workflows.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import uuid
from typing import TYPE_CHECKING

from . import __version__

if TYPE_CHECKING:
    from .scanner import ScanResult

# Map internal categories to CycloneDX component types.
_CDX_TYPE = {
    "model-artifact": "machine-learning-model",
    "model-provider": "library",
    "framework": "library",
    "orchestration": "library",
    "inference": "library",
    "vector-db": "library",
    "mlops": "library",
    "nlp": "library",
    "cv": "library",
    "audio": "library",
    "data": "data",
    "usage": "library",
    "unknown": "library",
}


def _bom_ref(*parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"aibom:{h}"


def _dedupe_components(components: list) -> list:
    """Deduplicate by name, preferring library > model-file > api-usage.

    Monorepos can produce multiple entries for the same package (e.g. 'openai'
    as both a library hit from requirements.txt and an api-usage hit from source).
    Keep the most informative entry per name.
    """
    _kind_order = {"library": 0, "model-file": 1, "api-usage": 2}
    seen: dict = {}
    for c in sorted(components, key=lambda x: _kind_order.get(x.kind, 99)):
        if c.name not in seen:
            seen[c.name] = c
    return list(seen.values())


def build_aibom(scan: "ScanResult", *, app_name: str = "target-application") -> dict:
    """Return a CycloneDX 1.6 AI-BOM dict for the given scan."""
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    hf_model_ids = getattr(scan, "hf_model_ids", [])

    components = []
    for c in _dedupe_components(scan.components):
        comp: dict = {
            "bom-ref": _bom_ref(c.name, c.kind, c.evidence),
            "type": _CDX_TYPE.get(c.category, "library"),
            "name": c.name,
            "scope": "required",
            "properties": [
                {"name": "aibom:kind", "value": c.kind},
                {"name": "aibom:category", "value": c.category},
                {"name": "aibom:evidence", "value": c.evidence},
            ],
        }
        if c.version:
            comp["version"] = c.version
        if c.vendor:
            comp["publisher"] = c.vendor
        if c.risk_note:
            comp["description"] = c.risk_note

        # Attach model card for model artifacts and NLP libraries that load HF models.
        if comp["type"] == "machine-learning-model" or c.category in ("model-provider", "nlp"):
            model_card: dict = {
                "modelParameters": {"task": {"type": "unknown"}},
                "quantitativeAnalysis": {},
                "considerations": {
                    "ethicalConsiderations": [],
                    "fairnessAssessments": [],
                    "_todo": "Populate training data, intended use, and limitations.",
                },
            }
            # Populate with HF model IDs detected in source (Milestone 1)
            if hf_model_ids and c.category in ("nlp", "model-artifact"):
                model_card["modelParameters"]["modelIds"] = list(hf_model_ids)
                model_card["modelParameters"]["task"]["type"] = "inferred-from-source"
            comp["modelCard"] = model_card

        components.append(comp)

    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": now,
            "tools": [{
                "vendor": "AIBOM-Guard",
                "name": "aibom-guard",
                "version": __version__,
            }],
            "component": {
                "bom-ref": _bom_ref(app_name, "root"),
                "type": "application",
                "name": app_name,
            },
            "properties": [
                {"name": "aibom:files_scanned", "value": str(scan.files_scanned)},
                {"name": "aibom:component_count", "value": str(len(components))},
                {"name": "aibom:hf_model_ids", "value": ",".join(hf_model_ids) or "none"},
            ],
        },
        "components": components,
    }
    return bom


def build_spdx(scan: "ScanResult", *, app_name: str = "target-application") -> dict:
    """Return an SPDX 3.0 AI-BOM dict for the given scan.

    Follows the SPDX 3.0 JSON-LD format with AI Profile extensions.
    See: https://spdx.github.io/spdx-spec/v3.0/
    """
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    hf_model_ids = getattr(scan, "hf_model_ids", [])
    root_id = f"https://aibom-guard/pkg/{app_name}"

    elements: list[dict] = [{
        "type": "software_Package",
        "spdxId": root_id,
        "name": app_name,
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": False,
        "comment": f"files_scanned={scan.files_scanned} components={len(scan.components)}",
    }]
    relationships: list[dict] = []

    for c in _dedupe_components(scan.components):
        elem_id = f"https://aibom-guard/pkg/{_bom_ref(c.name, c.kind, c.evidence)}"
        is_model = c.kind == "model-file" or c.category in ("nlp", "model-provider")

        pkg: dict = {
            "type": "ai_AIPackage" if is_model else "software_Package",
            "spdxId": elem_id,
            "name": c.name,
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "comment": f"kind={c.kind} category={c.category}",
        }
        if c.version:
            pkg["versionInfo"] = c.version
        if c.vendor:
            pkg["suppliedBy"] = [{"type": "Organization", "name": c.vendor}]
        if c.risk_note:
            pkg["comment"] = f"{pkg['comment']} risk_note={c.risk_note}"

        # AI Profile extensions for model components
        if is_model and hf_model_ids and c.category in ("nlp", "model-artifact"):
            pkg["ai_modelCard"] = {
                "ai_modelIds": list(hf_model_ids),
                "ai_hyperparameter": [],
                "_todo": "Populate model card fields per SPDX AI Profile",
            }

        elements.append(pkg)
        relationships.append({
            "type": "Relationship",
            "relationshipType": "CONTAINS",
            "from": root_id,
            "to": [elem_id],
        })

    return {
        "spdxVersion": "SPDX-3.0",
        "dataLicense": "CC0-1.0",
        "SPDXID": f"https://aibom-guard/doc/{uuid.uuid4()}",
        "name": f"{app_name}-ai-bom",
        "creationInfo": {
            "created": now,
            "createdBy": [{"type": "Tool", "name": f"aibom-guard-{__version__}"}],
            "specVersion": "3.0",
        },
        "elements": elements,
        "relationships": relationships,
    }
