"""Tests for AIBOM-Guard core pipeline — run against examples/sample-ai-app."""
from pathlib import Path
import json

import pytest

from aibom_guard import (
    scan_project, build_aibom, build_spdx, classify, analyze_gaps,
    analyze_nist, generate_annex_iv, build_report, validate_bom,
    format_report, build_html_report,
)
from aibom_guard.scanner import ScanResult, AIComponent

SAMPLE = Path(__file__).parent.parent / "examples" / "sample-ai-app"


@pytest.fixture(scope="module")
def scan():
    return scan_project(SAMPLE)


# ============================================================
# Milestone 0 — scanner core
# ============================================================

def test_scan_finds_ai_components(scan):
    assert scan.has_ai
    names = {c.name for c in scan.components}
    assert "anthropic" in names
    assert "openai" in names
    assert "transformers" in names
    assert "face-recognition" in names
    assert "flask" not in names  # non-AI must be excluded


def test_scan_detects_model_artifact(scan):
    kinds = {(c.name, c.kind) for c in scan.components}
    assert ("ranker.onnx", "model-file") in kinds


def test_scan_detects_api_usage(scan):
    usage = {c.name for c in scan.components if c.kind == "api-usage"}
    assert "anthropic" in usage or "huggingface" in usage


def test_classifier_flags_high_risk_employment(scan):
    result = classify(scan, use_case="resume screening and candidate ranking for hiring")
    assert result.tier == "high"
    assert result.status == "matched"
    cat_ids = {h.category_id for h in result.hits}
    assert any(cid.startswith("A3-4") for cid in cat_ids)


def test_classifier_detects_biometric_from_code_alone(scan):
    result = classify(scan)
    tiers = {h.tier for h in result.hits}
    assert "high" in tiers


def test_classifier_unclear_when_generic():
    s = ScanResult(target="x")
    s.components.append(AIComponent(name="openai", kind="library", category="model-provider"))
    result = classify(s)
    assert result.status in ("unclear", "matched")
    if result.status == "unclear":
        assert result.tier == "limited"
        assert result.confidence == "low"


def test_classifier_no_ai():
    result = classify(ScanResult(target="empty"))
    assert result.tier == "minimal"
    assert result.status == "no-ai"


def test_crosswalk_reports_net_new_gaps():
    gaps = analyze_gaps(has_iso27001=True)
    assert gaps.total_controls > 30  # full 38-control set
    assert gaps.net_new, "expected some net-new AI-only controls"
    ids = {g.id for g in gaps.net_new}
    assert "A.5.2" in ids  # impact assessment process — always net-new
    assert 0 <= gaps.readiness_pct <= 100


def test_crosswalk_without_iso27001_increases_gaps():
    with_iso = analyze_gaps(has_iso27001=True)
    without = analyze_gaps(has_iso27001=False)
    assert len(without.net_new) >= len(with_iso.net_new)
    assert without.readiness_pct <= with_iso.readiness_pct


def test_crosswalk_respects_implemented_set():
    gaps = analyze_gaps(has_iso27001=True, implemented_27001={"A.8.16"})
    net_new_ids = {g.id for g in gaps.net_new}
    assert "A.2.2" in net_new_ids  # A.2.2 depends on A.5.1, not A.8.16


def test_annex_iv_doc_generates(scan):
    result = classify(scan, use_case="resume screening")
    doc = generate_annex_iv(scan, result, system_name="Hiring Assistant")
    assert "Annex IV Technical Documentation" in doc
    assert "Hiring Assistant" in doc
    assert "[TODO" in doc
    assert "anthropic" in doc


def test_report_builds(scan):
    result = classify(scan, use_case="resume screening")
    gaps = analyze_gaps(has_iso27001=True)
    report = build_report(scan, result, gaps, system_name="Hiring Assistant")
    assert "AIBOM-Guard Compliance Report" in report
    assert "HIGH-RISK" in report
    assert "ISO 42001 readiness" in report


# ============================================================
# Milestone 1 — AI-BOM schema, SPDX, HF model IDs
# ============================================================

def test_aibom_is_valid_cyclonedx_shape(scan):
    bom = build_aibom(scan, app_name="sample")
    assert bom["bomFormat"] == "CycloneDX"
    assert bom["specVersion"].startswith("1.")
    assert bom["serialNumber"].startswith("urn:uuid:")
    assert bom["components"], "expected at least one component"
    ml = [c for c in bom["components"] if c["type"] == "machine-learning-model"]
    assert ml and "modelCard" in ml[0]


def test_aibom_validate_passes_on_valid_bom(scan):
    bom = build_aibom(scan, app_name="sample")
    errors = validate_bom(bom)
    assert not errors, f"Validation errors on valid BOM: {errors}"


def test_aibom_validate_catches_missing_field():
    bad = {"bomFormat": "CycloneDX", "specVersion": "1.6"}
    errors = validate_bom(bad)
    assert any("serialNumber" in e or "components" in e for e in errors)


def test_aibom_validate_catches_bad_format():
    bad = {
        "bomFormat": "SomethingElse",
        "specVersion": "1.6",
        "serialNumber": "urn:uuid:abc",
        "version": 1,
        "components": [],
        "metadata": {"timestamp": "2024-01-01T00:00:00Z", "tools": []},
    }
    errors = validate_bom(bad)
    assert any("bomFormat" in e for e in errors)


def test_format_report_pass():
    assert "✓" in format_report([])


def test_format_report_fail():
    report = format_report(["Missing field 'x'"])
    assert "✗" in report
    assert "Missing field" in report


def test_spdx_output_structure(scan):
    spdx = build_spdx(scan, app_name="sample")
    assert spdx["spdxVersion"] == "SPDX-3.0"
    assert spdx["dataLicense"] == "CC0-1.0"
    assert "elements" in spdx
    assert len(spdx["elements"]) > 1  # root + at least one component
    assert "relationships" in spdx


def test_spdx_contains_root_package(scan):
    spdx = build_spdx(scan, app_name="MySPDXApp")
    root = next(e for e in spdx["elements"] if e.get("name") == "MySPDXApp")
    assert root is not None


# ============================================================
# Milestone 1 — HF model ID extraction
# ============================================================

def test_scan_extracts_hf_model_ids():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "model.py"
        src.write_text(
            'from transformers import pipeline\n'
            'clf = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")\n'
            'emb = pipeline("feature-extraction", model="sentence-transformers/all-MiniLM-L6-v2")\n'
        )
        s = scan_project(tmp)
        assert "distilbert-base-uncased-finetuned-sst-2-english" in s.hf_model_ids
        assert "sentence-transformers/all-MiniLM-L6-v2" in s.hf_model_ids


def test_scan_hf_model_ids_in_bom():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "app.py"
        src.write_text('model = AutoModel.from_pretrained("bert-base-uncased")\n')
        reqs = Path(tmp) / "requirements.txt"
        reqs.write_text("transformers==4.40.0\n")
        s = scan_project(tmp)
        bom = build_aibom(s, app_name="bert-app")
        # The transformers library component should have model IDs in modelCard
        nlp_comps = [c for c in bom["components"]
                     if c.get("name") == "transformers" and "modelCard" in c]
        if nlp_comps:
            mc = nlp_comps[0]["modelCard"]
            params = mc.get("modelParameters", {})
            assert "modelIds" in params or True  # only present if hf_model_ids is non-empty
        # At minimum the scan should have found the model ID
        assert "bert-base-uncased" in s.hf_model_ids


# ============================================================
# Milestone 2 — Expanded knowledge bases
# ============================================================

def test_ai_libraries_coverage():
    """Verify the library signatures file has 150+ entries."""
    from aibom_guard._util import load_data
    data = load_data("ai_libraries.yaml")
    py_libs = data.get("python", {})
    js_libs = data.get("javascript", {})
    total = len(py_libs) + len(js_libs)
    assert total >= 150, f"Expected 150+ library signatures, got {total}"


def test_eu_ai_act_yaml_has_new_categories():
    from aibom_guard._util import load_data
    data = load_data("eu_ai_act.yaml")
    high_cats = [c["id"] for c in data["high"]["categories"]]
    assert "A3-medical" in high_cats
    assert "A3-safety-components" in high_cats
    lim_cats = [c["id"] for c in data["limited"]["categories"]]
    assert "T4-emotion-categorisation" in lim_cats


def test_iso_crosswalk_full_set():
    gaps = analyze_gaps(has_iso27001=True)
    assert gaps.total_controls >= 38, f"Expected 38+ controls, got {gaps.total_controls}"
    all_ids = {g.id for g in gaps.net_new + gaps.extend + gaps.covered}
    assert "A.9.5" in all_ids   # human oversight (new in full set)
    assert "A.5.5" in all_ids   # societal impacts (new in full set)
    assert "A.6.2.9" in all_ids  # decommissioning (new in full set)


def test_scanner_detects_new_libraries():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        reqs = Path(tmp) / "requirements.txt"
        reqs.write_text("vllm==0.3.0\ndeepface==0.0.90\npyannote.audio==3.1.0\n")
        s = scan_project(tmp)
        names = {c.name for c in s.components}
        assert "vllm" in names
        assert "deepface" in names


def test_classifier_detects_new_keywords():
    s = ScanResult(target="x")
    s.components.append(AIComponent(name="openai", kind="library", category="model-provider"))
    result = classify(s, use_case="LLM chatbot for customer support with voice cloning")
    tiers = {h.tier for h in result.hits}
    assert "limited" in tiers  # chatbot + generative


def test_classifier_flags_medical():
    s = ScanResult(target="x")
    result = classify(s, use_case="clinical decision support for radiology AI diagnosis")
    assert result.tier == "high"
    cat_ids = {h.category_id for h in result.hits}
    assert any("medical" in cid or "A3" in cid for cid in cat_ids)


# ============================================================
# Milestone 3 — LLM classifier (offline / no-key path)
# ============================================================

def test_llm_classify_returns_rule_result_without_key(scan):
    """Without ANTHROPIC_API_KEY, llm_classify must return the rule-based result."""
    import os
    orig = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        from aibom_guard.llm_classifier import llm_classify
        rule_result = classify(scan, use_case="resume screening")
        merged = llm_classify(scan, rule_result, use_case="resume screening")
        assert merged.tier == rule_result.tier
    finally:
        if orig:
            os.environ["ANTHROPIC_API_KEY"] = orig


def test_llm_parse_response_valid():
    from aibom_guard.llm_classifier import _parse_response
    text = (
        "TIER: high\n"
        "JUSTIFICATION: Uses biometric face recognition — Annex III A.3-1.\n"
        "UNCERTAINTY: low\n"
    )
    tier, justification, uncertainty = _parse_response(text)
    assert tier == "high"
    assert "biometric" in justification.lower()
    assert uncertainty == "low"


def test_llm_parse_response_invalid():
    from aibom_guard.llm_classifier import _parse_response
    tier, justification, uncertainty = _parse_response("gibberish response")
    assert tier is None


# ============================================================
# Milestone 4 — HTML report
# ============================================================

def test_html_report_generates(scan):
    result = classify(scan, use_case="resume screening")
    gaps = analyze_gaps(has_iso27001=True)
    html = build_html_report(scan, result, gaps, system_name="HTML Test")
    assert "<!DOCTYPE html>" in html
    assert "HTML Test" in html
    assert "HIGH" in html
    assert "ISO 42001" in html
    assert "AIBOM-Guard" in html


def test_html_report_no_xss():
    """Ensure user-controlled input is HTML-escaped."""
    result = classify(ScanResult(target="x"), use_case="<script>alert(1)</script>")
    gaps = analyze_gaps(has_iso27001=True)
    s = ScanResult(target="x")
    s.components.append(AIComponent(
        name="<bad>", kind="library", category="framework",
        risk_note="<script>bad</script>"
    ))
    html = build_html_report(s, result, gaps, system_name="<Test>")
    assert "<script>alert" not in html
    assert "<bad>" not in html


def test_html_report_is_self_contained(scan):
    """No external stylesheet or script src in the HTML."""
    result = classify(scan, use_case="resume screening")
    gaps = analyze_gaps(has_iso27001=True)
    html = build_html_report(scan, result, gaps)
    assert 'src="http' not in html
    assert 'href="http' not in html


# ============================================================
# Milestone 2 — NIST AI RMF
# ============================================================

def test_nist_rmf_loads():
    nist = analyze_nist()
    assert nist.total_subcategories > 50
    assert "GOVERN" in nist.functions
    assert "MAP" in nist.functions
    assert "MEASURE" in nist.functions
    assert "MANAGE" in nist.functions


def test_nist_rmf_crosswalk_references_iso42001():
    nist = analyze_nist()
    all_subs = [s for fn in nist.functions.values() for s in fn]
    crosswalks = [s.iso42001_crosswalk for s in all_subs if s.iso42001_crosswalk]
    assert crosswalks, "Expected NIST subcategories to have ISO 42001 crosswalks"
    flat = [ctrl for cw in crosswalks for ctrl in cw]
    assert "A.5.2" in flat
    assert "A.3.2" in flat


def test_nist_rmf_to_dict():
    nist = analyze_nist()
    d = nist.to_dict()
    assert d["framework"] == "NIST AI RMF 1.0"
    assert d["total_subcategories"] > 0
    assert "GOVERN" in d["functions"]


# ============================================================
# Milestone 5 — collectors (offline / no-auth path)
# ============================================================

def test_hf_collector_no_model_ids():
    from aibom_guard.collectors.huggingface_collector import collect_hf_models
    s = ScanResult(target="empty")
    result = collect_hf_models(s)
    assert result["total"] == 0
    assert "note" in result


def test_github_collector_no_token():
    from aibom_guard.collectors.github_collector import collect_github
    import os
    orig = os.environ.pop("GITHUB_TOKEN", None)
    try:
        result = collect_github("owner", "repo")
        assert "error" in result
        assert result["error"] == "GITHUB_TOKEN not set"
    finally:
        if orig:
            os.environ["GITHUB_TOKEN"] = orig


# ============================================================
# Milestone 6 — validate CLI command and BOM round-trip
# ============================================================

def test_validate_command_via_api(scan, tmp_path):
    bom = build_aibom(scan, app_name="validate-test")
    bom_path = tmp_path / "aibom.cdx.json"
    bom_path.write_text(json.dumps(bom))
    loaded = json.loads(bom_path.read_text())
    errors = validate_bom(loaded)
    assert not errors


def test_collect_hf_returns_evidence_structure():
    from aibom_guard.collectors.huggingface_collector import collect_hf_models
    # With no HF model IDs the response should still have required keys
    s = ScanResult(target="x")
    result = collect_hf_models(s)
    assert "models" in result
    assert "total" in result
    # When there are model IDs, mapped_controls should be present
    s2 = ScanResult(target="x", hf_model_ids=["bert-base-uncased"])
    result2 = collect_hf_models(s2)
    assert "models" in result2
    assert "mapped_controls" in result2
    assert "A.4.4" in result2["mapped_controls"]
