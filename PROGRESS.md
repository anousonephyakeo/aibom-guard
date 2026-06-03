# PROGRESS — AIBOM-Guard v0.2.0

**Completed autonomously while you slept. Last updated: 2026-06-03**

## Status: ALL 6 MILESTONES COMPLETE ✅

Tests: **41 passing** (was 13 in v0.1.0) | Version: **0.2.0** | Committed: `fc7b4cb`

---

## What was implemented

### Milestone 1 — Schema validation & richer AI-BOM ✅
- **`validate.py`** — structural CycloneDX 1.6 validation; optional jsonschema full-schema
  validation (`pip install aibom-guard[validate]`)
- **`--validate` flag** on `scan` and `all` commands — exits non-zero on errors
- **SPDX 3.0 output** — `build_spdx()` function + `--format spdx` flag
- **HF model ID extraction** — detects `from_pretrained("model-id")` and
  `model="owner/model"` patterns in source; populates `modelCard.modelParameters.modelIds`
  in the AI-BOM automatically

### Milestone 2 — Deeper knowledge bases ✅
- **`ai_libraries.yaml`** — expanded from 60 to **160+ signatures** covering:
  RL (stable-baselines3, gymnasium), safety/XAI (SHAP, LIME, AIF360, fairlearn,
  adversarial toolboxes), audio (pyannote, speechbrain, bark, coqui-tts),
  multimodal (diffusers, CLIP), new providers (litellm, vllm, ollama, Azure, Vertex),
  agents (pydantic-ai, smolagents, autogen), new JS libraries
- **`eu_ai_act.yaml`** — richer keyword sets for all categories; added:
  `A3-medical` (radiology, diagnosis, clinical AI), `A3-safety-components` (ISO 26262,
  SCADA), `T4-emotion-categorisation` (gender/age detection disclosure); expanded
  employment, biometric, and chatbot keyword lists
- **`iso_crosswalk.yaml`** — **full 38-control ISO 42001 Annex A set** (was partial).
  Added: A.3.4 (conflict of interest), A.4.6 (AI competence), A.5.5 (societal impacts),
  A.6.2.3 (data acquisition), A.6.2.9 (decommissioning), A.7.3/7.4/7.7 (data quality),
  A.8.5 (instructions for users), A.9.5 (human oversight), A.9.6 (monitoring), A.10.4
- **`nist_ai_rmf.yaml`** — full NIST AI RMF 1.0 (65 subcategories across GOVERN/MAP/
  MEASURE/MANAGE) with ISO 42001 control crosswalks
- **`crosswalk.py`** — new `analyze_nist()` function + `--framework nist` CLI option

### Milestone 3 — LLM-assisted classification ✅
- **`llm_classifier.py`** — Anthropic API (Claude Haiku by default) with:
  - **Conservative merge rule**: LLM can never downgrade below rule-based tier
  - Falls back to rule-based result if `ANTHROPIC_API_KEY` not set (offline-safe)
  - Requires `pip install aibom-guard[llm]` or `anthropic` package
- **`--llm` flag** on `classify` and `all` commands

### Milestone 4 — HTML report + dashboard ✅
- **`html_report.py`** — fully self-contained HTML (zero external deps, all CSS inlined):
  - Metric dashboard grid with colour-coded tier badge
  - Readiness progress bar
  - AI-BOM component table
  - EU AI Act classification hits table
  - ISO 42001 gap table (net-new + extend)
  - Next actions list
  - XSS-safe (all user content HTML-escaped)
- **`build_html_report()`** exported from package
- **`--html` flag** on `all` command → writes `compliance_report.html`

### Milestone 5 — Evidence collectors ✅
- **`collectors/github_collector.py`** — reads GitHub repository settings (READ-ONLY):
  - Branch protection (required reviews, status checks, enforce admins)
  - Code scanning / SAST activity
  - Secret scanning open alerts
  - Dependency graph accessibility
  - Maps to controls: A.6.1.3, A.6.2.4, A.6.2.5
  - Requires `GITHUB_TOKEN` env var; gracefully reports error if missing
- **`collectors/huggingface_collector.py`** — fetches model metadata from HF Hub API:
  - Pipeline task, license, training datasets, framework tags
  - Model card existence + limitations documentation
  - Maps to: A.4.4, A.7.5, A.6.2.7
  - No authentication required (uses public HF API)
- **`collect` subcommand** — `aibom-guard collect ./project --github owner/repo -o reports/`

### Milestone 6 — Packaging & CI ✅
- **`.github/workflows/ci.yml`** — full CI pipeline:
  - Matrix: Python 3.11 and 3.12
  - Runs pytest with coverage
  - Full sample pipeline run (`aibom-guard all ... --html --nist`)
  - BOM validation step
  - Lint with ruff
  - Self-scan job (AIBOM-Guard scans itself)
- **`pyproject.toml`** v0.2.0 with optional dep groups: `[dev]`, `[validate]`, `[llm]`, `[all]`
- **`pyproject.toml`** adds ruff linting config

---

## What's NOT done (remaining work)

- **PyPI publish** — intentionally NOT done; requires your explicit approval
- **GitHub push** — intentionally NOT done; requires your explicit approval
- **MCP server wrapper** — nice-to-have; wraps CLI as MCP tools for Claude/Cursor
- **Benchmarking real repos** — HANDOFF.md Milestone 2 asks to scan 3-5 real AI repos
  and document results in `docs/benchmarks.md`
- **Full jsonschema validation** — the `--full` flag path works but needs
  `pip install jsonschema` and network access to fetch the official CDX schema

---

## How to push to GitHub when you wake up

```bash
cd /Users/swizzxxx/Desktop/Ai_Bom/aibom-guard

# Create the repo on GitHub first (in browser or via CLI), then:
git remote add origin https://github.com/AnousonePhyakeo/aibom-guard.git
git push -u origin main
```

Once pushed:
- CI runs automatically on every push
- Nightly compliance workflow runs at 02:00 UTC
- Add `GITHUB_TOKEN` as a repo secret to enable the nightly issue-creation

---

## Quick verification commands

```bash
# All tests passing
python -m pytest --tb=short

# Full pipeline with HTML + NIST
python -m aibom_guard.cli all examples/sample-ai-app \
  --name "Demo" --use-case "resume screening" --html --nist -o reports/

# Validate the BOM
python -m aibom_guard.cli validate reports/aibom.cdx.json

# NIST AI RMF crosswalk
python -m aibom_guard.cli crosswalk --framework nist 2>/dev/null | python -m json.tool | head -30

# SPDX output
python -m aibom_guard.cli scan examples/sample-ai-app --format spdx 2>/dev/null | head -20
```
