"""Read-only HuggingFace Hub model evidence collector.

For each HuggingFace model ID detected in a scan, fetches:
  - Pipeline task (text-classification, token-classification, etc.)
  - License (from model card or tags)
  - Training datasets (if declared in model card)
  - Framework tags (pytorch, tensorflow, onnx, etc.)
  - Whether a model card / limitations section exists

No authentication required — uses the public HuggingFace Hub REST API.
Rate limit: ~300 requests/hour for anonymous requests (sufficient for most scans).

Findings map to ISO 42001 controls A.4.4 (tooling inventory),
A.7.5 (data provenance), and A.6.2.7 (technical documentation).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..scanner import ScanResult

_HF_API = "https://huggingface.co/api/models"
_TIMEOUT = 10
_KNOWN_FRAMEWORKS = frozenset({
    "pytorch", "tensorflow", "jax", "flax", "onnx",
    "safetensors", "transformers", "keras",
})


def collect_hf_models(scan: "ScanResult") -> dict:
    """Fetch compliance-relevant metadata for all HF model IDs in the scan.

    Returns a dict with a ``models`` list (one entry per model ID) and a
    ``mapped_controls`` section explaining which ISO 42001 controls are served.
    """
    model_ids = getattr(scan, "hf_model_ids", [])
    if not model_ids:
        return {
            "models": [],
            "total": 0,
            "note": "No HuggingFace model IDs detected in scan.",
        }

    results = [_fetch_model(mid) for mid in model_ids]

    return {
        "models": results,
        "total": len(results),
        "models_with_license": sum(1 for m in results if m.get("license", "unknown") != "unknown"),
        "models_with_card": sum(1 for m in results if m.get("model_card_exists")),
        "models_with_datasets": sum(1 for m in results if m.get("training_datasets")),
        "mapped_controls": {
            "A.4.4": "Tooling resources — AI component/model inventory",
            "A.7.5": "Data provenance — training dataset identification",
            "A.6.2.7": "Technical documentation — model cards and metadata",
        },
    }


def _fetch_model(model_id: str) -> dict:
    url = f"{_HF_API}/{model_id}"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "aibom-guard", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read())

        return {
            "model_id": model_id,
            "pipeline_tag": data.get("pipeline_tag") or "unknown",
            "license": _extract_license(data),
            "training_datasets": _extract_datasets(data),
            "framework_tags": [
                t for t in (data.get("tags") or []) if t in _KNOWN_FRAMEWORKS
            ],
            "downloads_month": data.get("downloads"),
            "private": data.get("private", False),
            "created_at": data.get("createdAt"),
            "model_card_exists": bool(data.get("cardData")),
            "limitations_documented": _check_limitations(data),
            "iso42001_evidence": {
                "A.4.4": "model_id detected in source; metadata fetched from HF Hub",
                "A.7.5": f"training_datasets: {_extract_datasets(data) or ['not declared']}",
                "A.6.2.7": f"model_card_exists={bool(data.get('cardData'))}",
            },
        }
    except urllib.error.HTTPError as e:
        return {
            "model_id": model_id,
            "error": f"HTTP {e.code}",
            "note": "Model may be private, gated, or not found on HF Hub",
        }
    except Exception as e:
        return {"model_id": model_id, "error": str(e)}


def _extract_license(data: dict) -> str:
    for tag in data.get("tags") or []:
        if isinstance(tag, str) and tag.startswith("license:"):
            return tag[8:]
    card = data.get("cardData") or {}
    lic = card.get("license")
    if isinstance(lic, list):
        return ", ".join(str(l) for l in lic)
    return str(lic) if lic else "unknown"


def _extract_datasets(data: dict) -> list[str]:
    card = data.get("cardData") or {}
    datasets = card.get("datasets", [])
    if isinstance(datasets, list):
        return [str(d) for d in datasets[:10]]
    return []


def _check_limitations(data: dict) -> bool:
    card_str = str(data.get("cardData", {})).lower()
    return any(
        kw in card_str
        for kw in ("limitation", "bias", "misuse", "restriction", "out-of-scope")
    )
