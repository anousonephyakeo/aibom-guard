"""AIBOM-Guard command-line interface.

Examples
--------
    aibom-guard scan      ./my-project [--validate] [--format spdx]
    aibom-guard classify  ./my-project --use-case "resume screening" [--llm]
    aibom-guard crosswalk [--no-iso27001] [--framework nist]
    aibom-guard docgen    ./my-project --name "Hiring Assistant"
    aibom-guard collect   ./my-project --github owner/repo
    aibom-guard all       ./my-project --use-case "credit scoring" -o ./reports [--html]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .scanner import scan_project
from .aibom import build_aibom, build_spdx
from .classifier import classify
from .crosswalk import analyze_gaps, analyze_nist
from .annex_iv import generate_annex_iv
from .report import build_report
from .validate import validate_bom, format_report
from .html_report import build_html_report


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _parse_implemented(arg: str | None) -> set[str] | None:
    if not arg:
        return None
    return {x.strip() for x in arg.split(",") if x.strip()}


def cmd_scan(args) -> int:
    scan = scan_project(args.target)
    fmt = getattr(args, "format", "cdx")

    if fmt == "spdx":
        bom = build_spdx(scan, app_name=args.name)
        filename = "aibom.spdx.json"
    else:
        bom = build_aibom(scan, app_name=args.name)
        filename = "aibom.cdx.json"

    # Validation (CycloneDX only; SPDX validation is future work)
    if getattr(args, "validate", False) and fmt != "spdx":
        errors = validate_bom(bom, use_jsonschema=False)
        report = format_report(errors, bom_name=filename)
        print(report, file=sys.stderr)
        if errors:
            return 2

    if args.output:
        out = Path(args.output)
        _write(out / filename, json.dumps(bom, indent=2))
        _write(out / "scan.json", json.dumps(scan.to_dict(), indent=2))
        print(f"AI-BOM written to {out / filename}")
        if scan.hf_model_ids:
            print(f"HuggingFace model IDs detected: {', '.join(scan.hf_model_ids)}")
    else:
        print(json.dumps(bom, indent=2))

    print(
        f"\n[scan] {len(scan.components)} AI component(s), "
        f"{scan.files_scanned} source/doc file(s) scanned, "
        f"{len(scan.hf_model_ids)} HF model ID(s) found.",
        file=sys.stderr,
    )
    return 0


def cmd_classify(args) -> int:
    scan = scan_project(args.target)
    result = classify(scan, use_case=args.use_case)

    if getattr(args, "llm", False):
        from .llm_classifier import llm_classify
        result = llm_classify(scan, result, use_case=args.use_case)

    print(json.dumps(result.to_dict(), indent=2))
    print(
        f"\n[classify] tier={result.tier} status={result.status} "
        f"confidence={result.confidence}",
        file=sys.stderr,
    )
    return 0


def cmd_crosswalk(args) -> int:
    framework = getattr(args, "framework", "iso42001")

    if framework == "nist":
        nist = analyze_nist()
        print(json.dumps(nist.to_dict(), indent=2))
        print(
            f"\n[crosswalk/nist] {nist.total_subcategories} subcategories across "
            f"{len(nist.functions)} functions",
            file=sys.stderr,
        )
    else:
        gaps = analyze_gaps(
            has_iso27001=not args.no_iso27001,
            implemented_27001=_parse_implemented(args.implemented),
        )
        print(json.dumps(gaps.to_dict(), indent=2))
        print(
            f"\n[crosswalk] readiness={gaps.readiness_pct}% "
            f"net_new={len(gaps.net_new)} extend={len(gaps.extend)}",
            file=sys.stderr,
        )
    return 0


def cmd_validate(args) -> int:
    """Validate a CycloneDX BOM JSON file."""
    path = Path(args.bom_file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1
    try:
        bom = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"error: could not parse JSON: {e}", file=sys.stderr)
        return 1

    errors = validate_bom(bom, use_jsonschema=getattr(args, "full", False))
    print(format_report(errors, bom_name=path.name))
    return 0 if not errors else 2


def cmd_docgen(args) -> int:
    scan = scan_project(args.target)
    result = classify(scan, use_case=args.use_case)
    doc = generate_annex_iv(scan, result, system_name=args.name)
    if args.output:
        out = _write(Path(args.output) / "annex_iv.md", doc)
        print(f"Annex IV draft written to {out}")
    else:
        print(doc)
    return 0


def cmd_collect(args) -> int:
    """Run live evidence collectors."""
    scan = scan_project(args.target)
    results: dict = {"target": args.target, "collectors": {}}

    # HuggingFace collector (no auth required)
    from .collectors.huggingface_collector import collect_hf_models
    hf = collect_hf_models(scan)
    results["collectors"]["huggingface"] = hf
    print(
        f"[collect/hf] {hf['total']} model(s) fetched "
        f"({hf.get('models_with_card', 0)} with model card)",
        file=sys.stderr,
    )

    # GitHub collector (requires GITHUB_TOKEN)
    gh_repo = getattr(args, "github", None)
    if gh_repo:
        if "/" not in gh_repo:
            print(
                "error: --github must be in owner/repo format", file=sys.stderr
            )
            return 1
        owner, repo = gh_repo.split("/", 1)
        from .collectors.github_collector import collect_github
        gh = collect_github(owner, repo)
        results["collectors"]["github"] = gh
        if "error" in gh:
            print(f"[collect/github] {gh['error']}", file=sys.stderr)
        else:
            print(
                f"[collect/github] collected {len(gh.get('controls', {}))} control(s) "
                f"for {owner}/{repo}",
                file=sys.stderr,
            )

    if args.output:
        out = Path(args.output)
        _write(out / "evidence.json", json.dumps(results, indent=2))
        print(f"Evidence written to {out / 'evidence.json'}")
    else:
        print(json.dumps(results, indent=2))

    return 0


def cmd_all(args) -> int:
    out = Path(args.output or "./reports")
    scan = scan_project(args.target)
    bom = build_aibom(scan, app_name=args.name)
    result = classify(scan, use_case=args.use_case)

    if getattr(args, "llm", False):
        from .llm_classifier import llm_classify
        result = llm_classify(scan, result, use_case=args.use_case)

    gaps = analyze_gaps(
        has_iso27001=not args.no_iso27001,
        implemented_27001=_parse_implemented(args.implemented),
    )
    report = build_report(scan, result, gaps, system_name=args.name)
    annex = generate_annex_iv(scan, result, system_name=args.name)

    # Validate BOM
    bom_errors = validate_bom(bom)
    validation_note = format_report(bom_errors, bom_name="aibom.cdx.json")

    # Optional SPDX output
    spdx = build_spdx(scan, app_name=args.name)

    _write(out / "aibom.cdx.json", json.dumps(bom, indent=2))
    _write(out / "aibom.spdx.json", json.dumps(spdx, indent=2))
    _write(out / "scan.json", json.dumps(scan.to_dict(), indent=2))
    _write(out / "classification.json", json.dumps(result.to_dict(), indent=2))
    _write(out / "iso42001_gaps.json", json.dumps(gaps.to_dict(), indent=2))
    _write(out / "annex_iv.md", annex)
    _write(out / "validation.txt", validation_note)
    report_path = _write(out / "compliance_report.md", report)

    # Optional HTML report
    if getattr(args, "html", False):
        html = build_html_report(scan, result, gaps, system_name=args.name)
        html_path = _write(out / "compliance_report.html", html)
        print(f"HTML report written to {html_path}")

    # Optional NIST crosswalk
    if getattr(args, "nist", False):
        nist = analyze_nist()
        _write(out / "nist_rmf.json", json.dumps(nist.to_dict(), indent=2))
        print(f"  - nist_rmf.json")

    print(f"Full compliance package written to {out.resolve()}/")
    for f in (
        "compliance_report.md", "aibom.cdx.json", "aibom.spdx.json",
        "classification.json", "iso42001_gaps.json", "annex_iv.md",
        "validation.txt", "scan.json",
    ):
        print(f"  - {f}")

    print(
        f"\n[all] tier={result.tier} ({result.status}) · "
        f"components={len(scan.components)} · "
        f"ISO42001 readiness={gaps.readiness_pct}% · "
        f"HF models={len(scan.hf_model_ids)}",
        file=sys.stderr,
    )
    print(validation_note, file=sys.stderr)

    if args.fail_on_high and result.tier in ("high", "prohibited"):
        print(
            f"\n::error:: EU AI Act tier '{result.tier}' — failing build "
            f"(--fail-on-high).",
            file=sys.stderr,
        )
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aibom-guard",
        description="AI Bill of Materials + EU AI Act / ISO 42001 / NIST AI RMF compliance triage.",
    )
    p.add_argument("--version", action="version", version=f"aibom-guard {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    def add_target(sp):
        sp.add_argument("target", help="Path to the project directory to scan")
        sp.add_argument(
            "-n", "--name", default="target-application",
            help="System/application name for the report",
        )

    # --- scan ---
    sp = sub.add_parser("scan", help="Scan and emit the AI-BOM (CycloneDX or SPDX)")
    add_target(sp)
    sp.add_argument("-o", "--output", help="Output directory (default: stdout)")
    sp.add_argument(
        "--format", choices=["cdx", "spdx"], default="cdx",
        help="Output format: cdx (CycloneDX 1.6) or spdx (SPDX 3.0)",
    )
    sp.add_argument(
        "--validate", action="store_true",
        help="Validate the emitted CycloneDX BOM structure (non-zero exit on errors)",
    )
    sp.set_defaults(func=cmd_scan)

    # --- classify ---
    sp = sub.add_parser("classify", help="Suggest the EU AI Act risk tier")
    add_target(sp)
    sp.add_argument("--use-case", help="Free-text description of what the system does")
    sp.add_argument(
        "--llm", action="store_true",
        help="Use LLM-assisted classification (requires ANTHROPIC_API_KEY)",
    )
    sp.set_defaults(func=cmd_classify)

    # --- crosswalk ---
    sp = sub.add_parser(
        "crosswalk",
        help="ISO 27001 → ISO 42001 gap analysis or NIST AI RMF listing",
    )
    sp.add_argument("--no-iso27001", action="store_true",
                    help="Org does NOT hold ISO 27001 (more gaps become net-new)")
    sp.add_argument(
        "--implemented",
        help="Comma-separated ISO 27001 control IDs actually implemented (e.g. 'A.5.1,A.8.16')",
    )
    sp.add_argument(
        "--framework", choices=["iso42001", "nist"], default="iso42001",
        help="Compliance framework to report (iso42001 or nist)",
    )
    sp.set_defaults(func=cmd_crosswalk)

    # --- validate ---
    sp = sub.add_parser("validate", help="Validate a CycloneDX BOM JSON file")
    sp.add_argument("bom_file", help="Path to the aibom.cdx.json file to validate")
    sp.add_argument(
        "--full", action="store_true",
        help="Attempt full JSON Schema validation (requires jsonschema + network)",
    )
    sp.set_defaults(func=cmd_validate)

    # --- docgen ---
    sp = sub.add_parser("docgen", help="Generate Annex IV technical-doc draft")
    add_target(sp)
    sp.add_argument("--use-case", help="Free-text description of what the system does")
    sp.add_argument("-o", "--output", help="Output directory (default: stdout)")
    sp.set_defaults(func=cmd_docgen)

    # --- collect ---
    sp = sub.add_parser("collect", help="Gather live compliance evidence from external systems")
    add_target(sp)
    sp.add_argument(
        "--github",
        metavar="OWNER/REPO",
        help="GitHub repo to collect evidence from (requires GITHUB_TOKEN env var)",
    )
    sp.add_argument("-o", "--output", help="Output directory (default: stdout)")
    sp.set_defaults(func=cmd_collect)

    # --- all ---
    sp = sub.add_parser("all", help="Run everything and write the full compliance package")
    add_target(sp)
    sp.add_argument("--use-case", help="Free-text description of what the system does")
    sp.add_argument("--no-iso27001", action="store_true")
    sp.add_argument("--implemented", help="Comma-separated ISO 27001 control IDs")
    sp.add_argument("-o", "--output", default="./reports", help="Output directory")
    sp.add_argument("--fail-on-high", action="store_true",
                    help="Exit non-zero if tier is high/prohibited (for CI gating)")
    sp.add_argument(
        "--html", action="store_true",
        help="Also generate a standalone HTML report (compliance_report.html)",
    )
    sp.add_argument(
        "--llm", action="store_true",
        help="Use LLM-assisted classification (requires ANTHROPIC_API_KEY)",
    )
    sp.add_argument(
        "--nist", action="store_true",
        help="Also generate a NIST AI RMF crosswalk (nist_rmf.json)",
    )
    sp.set_defaults(func=cmd_all)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
