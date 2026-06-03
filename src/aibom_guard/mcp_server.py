"""MCP server wrapper for AIBOM-Guard.

Exposes scan, classify, crosswalk, and validate as MCP tools so any
MCP-compatible agent (Claude Desktop, Cursor, etc.) can call them directly.

Usage:
    pip install "aibom-guard[mcp]"
    aibom-guard-mcp              # runs on stdio (MCP default)

Claude Desktop config (~/.claude_desktop_config.json):
    {
      "mcpServers": {
        "aibom-guard": {
          "command": "aibom-guard-mcp"
        }
      }
    }
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise ImportError(
        "MCP support requires: pip install 'aibom-guard[mcp]'"
    ) from exc

from . import (
    analyze_gaps,
    analyze_nist,
    build_aibom,
    build_report,
    classify,
    format_report,
    scan_project,
    validate_bom,
)

mcp = FastMCP("AIBOM-Guard — AI compliance triage for the EU AI Act & ISO 42001")


@mcp.tool()
def scan(path: str) -> str:
    """Scan a project directory for AI components.

    Returns a JSON summary of detected AI libraries, model files, and API
    usage patterns — the foundation for all subsequent compliance steps.
    """
    result = scan_project(path)
    return json.dumps(result.to_dict(), indent=2)


@mcp.tool()
def classify_risk(path: str, use_case: str = "") -> str:
    """Classify EU AI Act risk tier for a project.

    Args:
        path: Path to the project directory to scan.
        use_case: Natural-language description of what the system does
            (e.g. "resume screening for hiring"). More context → more accurate tier.

    Returns JSON with tier (prohibited/high/limited/minimal/unclear), confidence,
    matched categories, and a plain-English explanation.
    """
    scan_result = scan_project(path)
    result = classify(scan_result, use_case=use_case)
    return json.dumps({
        "tier": result.tier,
        "status": result.status,
        "confidence": result.confidence,
        "explanation": result.explanation,
        "hits": [
            {
                "category_id": h.category_id,
                "category_name": h.category_name,
                "tier": h.tier,
                "matched_keywords": h.matched_keywords,
            }
            for h in result.hits
        ],
    }, indent=2)


@mcp.tool()
def iso_gaps(has_iso27001: bool = True, implemented_controls: str = "") -> str:
    """Analyse ISO 42001 compliance gaps relative to an existing ISO 27001 baseline.

    Args:
        has_iso27001: Whether the organisation already holds ISO 27001.
        implemented_controls: Comma-separated ISO 27001 control IDs already
            implemented (e.g. "A.8.16,A.5.23"). Leave empty if unknown.

    Returns a JSON gap report: net-new AI controls, controls that extend existing
    27001 work, readiness percentage, and recommended next actions.
    """
    impl_set: set[str] = set()
    if implemented_controls.strip():
        impl_set = {c.strip() for c in implemented_controls.split(",") if c.strip()}
    gaps = analyze_gaps(has_iso27001=has_iso27001, implemented_27001=impl_set)
    return json.dumps({
        "readiness_pct": gaps.readiness_pct,
        "total_controls": gaps.total_controls,
        "net_new": [
            {"id": g.id, "title": g.title, "priority": g.priority}
            for g in gaps.net_new
        ],
        "extend": [{"id": g.id, "title": g.title} for g in gaps.extend],
        "next_actions": gaps.next_actions,
    }, indent=2)


@mcp.tool()
def nist_rmf() -> str:
    """Return the full NIST AI RMF 1.0 framework with ISO 42001 crosswalks.

    Covers all 65 subcategories across GOVERN, MAP, MEASURE, and MANAGE functions,
    each mapped to relevant ISO 42001 Annex A controls.
    """
    result = analyze_nist()
    return json.dumps(result.to_dict(), indent=2)


@mcp.tool()
def validate(bom_json: str) -> str:
    """Validate a CycloneDX AI-BOM JSON string for structural correctness.

    Args:
        bom_json: The full CycloneDX BOM as a JSON string.

    Returns a validation report: PASS with checkmark or FAIL with error list.
    """
    try:
        bom = json.loads(bom_json)
    except json.JSONDecodeError as exc:
        return f"INVALID JSON: {exc}"
    errors = validate_bom(bom)
    return format_report(errors)


@mcp.tool()
def full_report(path: str, use_case: str = "", system_name: str = "") -> str:
    """Run the full AIBOM-Guard pipeline and return a Markdown compliance report.

    This is the 'aibom-guard all' equivalent as a single MCP call.

    Args:
        path: Path to the project directory.
        use_case: What the AI system does (improves EU AI Act tier accuracy).
        system_name: Human-readable name for the system (appears in the report).

    Returns Markdown with: scan summary, EU AI Act tier, ISO 42001 gap table,
    NIST AI RMF coverage, next actions, and BOM validation result.
    """
    scan_result = scan_project(path)
    classification = classify(scan_result, use_case=use_case)
    gaps = analyze_gaps()
    bom = build_aibom(scan_result, app_name=system_name or Path(path).name)
    bom_errors = validate_bom(bom)
    report = build_report(
        scan_result, classification, gaps,
        system_name=system_name or Path(path).name,
    )
    bom_status = format_report(bom_errors)
    return f"{report}\n\n---\n**BOM Validation:** {bom_status.strip()}"


def main() -> None:
    """Entry point for the MCP server (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    main()
