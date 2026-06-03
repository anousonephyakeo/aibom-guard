"""Structural validation of CycloneDX 1.6 AI-BOMs.

Validates the required structural fields per the CycloneDX 1.6 specification.
Full JSON Schema validation is available when ``jsonschema`` is installed
(pip install aibom-guard[validate]) and network access is available.

Usage::

    from aibom_guard.validate import validate_bom, format_report
    errors = validate_bom(bom)
    print(format_report(errors))
"""
from __future__ import annotations

_REQUIRED_TOP = ("bomFormat", "specVersion", "serialNumber", "version", "components")
_REQUIRED_META_FIELDS = ("timestamp", "tools")
_REQUIRED_COMP = ("bom-ref", "type", "name")

_VALID_COMP_TYPES = frozenset({
    "application", "container", "device", "file", "firmware",
    "framework", "library", "machine-learning-model", "data",
    "platform", "service",
})
_VALID_SCOPES = frozenset({"required", "optional", "excluded"})

# CycloneDX 1.6 JSON schema URL (used when jsonschema + network available)
_CDX_SCHEMA_URL = (
    "https://raw.githubusercontent.com/CycloneDX/specification/"
    "1.6/schema/bom-1.6.schema.json"
)


def validate_bom(bom: dict, *, use_jsonschema: bool = False) -> list[str]:
    """Validate a CycloneDX 1.6 BOM dict.

    Returns a list of error strings; empty list means structurally valid.
    Set ``use_jsonschema=True`` for full schema validation (requires jsonschema
    package and network access to fetch the official CycloneDX schema).
    """
    errors: list[str] = []

    if not isinstance(bom, dict):
        return ["BOM must be a JSON object (dict)"]

    # Required top-level fields
    for f in _REQUIRED_TOP:
        if f not in bom:
            errors.append(f"Missing required top-level field: '{f}'")

    if bom.get("bomFormat") != "CycloneDX":
        errors.append(
            f"bomFormat must be 'CycloneDX', got: {bom.get('bomFormat')!r}"
        )

    spec = str(bom.get("specVersion", ""))
    if not spec.startswith("1."):
        errors.append(f"specVersion looks invalid: {spec!r} (expected '1.6')")

    sn = str(bom.get("serialNumber", ""))
    if not sn.startswith("urn:uuid:"):
        errors.append(
            f"serialNumber must start with 'urn:uuid:', got: {sn!r}"
        )

    ver = bom.get("version")
    if ver is not None and not isinstance(ver, int):
        errors.append(f"version must be an integer, got: {type(ver).__name__}")

    meta = bom.get("metadata", {})
    if isinstance(meta, dict):
        for f in _REQUIRED_META_FIELDS:
            if f not in meta:
                errors.append(f"metadata missing field: '{f}'")
    else:
        errors.append("metadata must be a JSON object")

    comps = bom.get("components", [])
    if not isinstance(comps, list):
        errors.append("components must be a JSON array")
    else:
        for i, comp in enumerate(comps):
            if not isinstance(comp, dict):
                errors.append(f"components[{i}] must be a JSON object")
                continue
            label = f"components[{i}] ({comp.get('name', '?')})"
            for f in _REQUIRED_COMP:
                if f not in comp:
                    errors.append(f"{label}: missing required field '{f}'")
            ctype = comp.get("type", "")
            if ctype not in _VALID_COMP_TYPES:
                errors.append(f"{label}: unknown component type {ctype!r}")
            scope = comp.get("scope")
            if scope is not None and scope not in _VALID_SCOPES:
                errors.append(f"{label}: unknown scope {scope!r}")

    if use_jsonschema:
        _try_jsonschema(bom, errors)

    return errors


def _try_jsonschema(bom: dict, errors: list[str]) -> None:
    try:
        import jsonschema  # type: ignore[import]
    except ImportError:
        errors.append(
            "[warn] jsonschema not installed; run `pip install jsonschema` "
            "for full schema validation"
        )
        return
    import json
    import urllib.request
    try:
        with urllib.request.urlopen(_CDX_SCHEMA_URL, timeout=8) as resp:  # nosec B310 — hardcoded HTTPS URL to cyclonedx.org schema
            schema = json.loads(resp.read())
        validator = jsonschema.Draft7Validator(schema)
        for err in validator.iter_errors(bom):
            path = " > ".join(str(p) for p in err.absolute_path) or "(root)"
            errors.append(f"[jsonschema] {path}: {err.message}")
    except Exception as exc:
        errors.append(f"[jsonschema] schema fetch/validation failed: {exc}")


def format_report(errors: list[str], bom_name: str = "BOM") -> str:
    """Return a human-readable validation summary string."""
    if not errors:
        return f"✓ {bom_name} is structurally valid (CycloneDX 1.6)."
    lines = [f"✗ {bom_name} has {len(errors)} validation issue(s):"]
    for i, e in enumerate(errors, 1):
        lines.append(f"  {i}. {e}")
    return "\n".join(lines)
