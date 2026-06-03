# AIBOM-Guard

**Generate an AI Bill of Materials, triage your EU AI Act risk tier, and turn an
existing ISO 27001 ISMS into ISO 42001 readiness — from the command line, in seconds.**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-42%20passing-brightgreen)](tests/)
[![CycloneDX](https://img.shields.io/badge/AI--BOM-CycloneDX%201.6-orange)](https://cyclonedx.org/)
[![SPDX](https://img.shields.io/badge/AI--BOM-SPDX%203.0-blue)](https://spdx.dev/)

> ⚖️ **AIBOM-Guard is a triage and documentation aid — not legal advice, an audit, or
> a conformity assessment.** All output should be confirmed by a qualified human.
> High-risk and prohibited results must be escalated to compliance/legal.

---

## Why this exists

The EU AI Act's obligations for high-risk systems become enforceable on **2 August 2026**.
Article 11 requires technical documentation, Article 12 requires event logging, and
ISO/IEC 42001 is becoming the framework organisations use to demonstrate it. Yet:

- Commercial AI-governance platforms cost tens of thousands per year.
- Fully automated AI-BOM generation barely existed in open source.
- Most teams holding **ISO 27001** have no idea what **ISO 42001** adds on top.

AIBOM-Guard closes that gap for engineers: point it at a repo, get a machine-readable AI
inventory, a provisional risk tier, a prioritised ISO 42001 gap list, an Annex IV draft,
and an HTML compliance report — all offline, no accounts required.

---

## What it does

| Capability | Output |
|---|---|
| 🔎 **AI component scan** | Detects 160+ AI libraries, model files, and API usage patterns across Python/JS |
| 📦 **AI-BOM generation** | CycloneDX 1.6 JSON **and** SPDX 3.0 AI Profile — both validated |
| ⚖️ **EU AI Act triage** | Provisional tier (prohibited / high / limited / minimal) with matched Annex III / Article 5 categories |
| 🧭 **ISO 42001 gap analysis** | Net-new vs extend vs covered controls; readiness % vs ISO 27001 baseline |
| 🗺️ **NIST AI RMF crosswalk** | Full 65-subcategory GOVERN/MAP/MEASURE/MANAGE framework with ISO 42001 crosswalks |
| 📄 **Annex IV docgen** | Structured technical-documentation draft, pre-filled and `[TODO]`-flagged |
| 🌐 **HTML report** | Self-contained, shareable compliance dashboard — no external dependencies |
| 🧠 **LLM-assisted classification** | Optional Claude Haiku second opinion; never downgrades a rule-based tier |
| 🔌 **Evidence collectors** | Read-only GitHub repo + HuggingFace Hub metadata → mapped to ISO 42001 controls |
| 🤖 **MCP server** | Wrap the CLI as MCP tools for Claude Desktop, Cursor, or any MCP-compatible agent |

---

## Quickstart

```bash
pip install aibom-guard           # or: pip install -e ".[dev]" from source

aibom-guard all ./my-ai-project \
  --name "Hiring Assistant" \
  --use-case "resume screening and candidate ranking for recruitment" \
  --html \
  -o reports/
```

`reports/` will contain:

| File | Contents |
|------|----------|
| `compliance_report.md` | Full Markdown compliance report |
| `compliance_report.html` | Self-contained HTML dashboard |
| `aibom.cdx.json` | CycloneDX 1.6 AI-BOM |
| `aibom.spdx.json` | SPDX 3.0 AI-BOM |
| `classification.json` | EU AI Act tier + evidence |
| `iso42001_gaps.json` | Gap analysis JSON |
| `annex_iv.md` | Annex IV technical documentation draft |
| `validation.txt` | BOM validation result |
| `scan.json` | Raw component inventory |

---

## Commands

### `all` — full compliance pipeline

```bash
aibom-guard all ./project \
  --name "My AI System" \
  --use-case "credit scoring for loan decisions" \
  --html           # HTML dashboard
  --nist           # include NIST AI RMF crosswalk
  --llm            # Claude Haiku second opinion (requires ANTHROPIC_API_KEY)
  --validate       # exit non-zero if BOM has errors
  -o reports/
```

### `scan` — AI component detection only

```bash
aibom-guard scan ./project -o reports/
aibom-guard scan ./project --format spdx -o reports/   # SPDX 3.0 output
aibom-guard scan ./project --validate                  # validate emitted BOM
```

### `classify` — EU AI Act tier

```bash
aibom-guard classify ./project --use-case "medical imaging for radiology"
aibom-guard classify ./project --use-case "resume screening" --llm
```

### `crosswalk` — ISO 42001 or NIST AI RMF gap analysis

```bash
aibom-guard crosswalk                          # ISO 42001 (default)
aibom-guard crosswalk --no-iso27001           # without ISO 27001 baseline
aibom-guard crosswalk --framework nist        # NIST AI RMF 1.0
```

### `validate` — BOM validation

```bash
aibom-guard validate reports/aibom.cdx.json
aibom-guard validate reports/aibom.cdx.json --full   # full JSON Schema check
```

### `collect` — evidence collectors

```bash
aibom-guard collect ./project \
  --github myorg/my-repo \   # maps branch protection / SAST / secret scanning to ISO 42001
  -o reports/
```

---

## Sample output

Running against the bundled demo app (resume screening + facial recognition) correctly
flags it as high-risk on two Annex III grounds:

```
EU AI Act tier (provisional)       🔴 HIGH-RISK
AI components detected             10
ISO 42001 readiness (vs 27001)     35%
ISO 42001 net-new controls         13

Matched categories:
  [high]    A3-1-biometrics  — biometric, facial recognition, face-recognition
  [high]    A3-4-employment  — resume screening, candidate ranking, hiring
  [limited] T1-chatbot       — openai, anthropic
```

---

## How it works

```
               ┌──────────────┐
  target repo ─►    scanner   ├─► AIComponent[]  (160+ sigs, 13 API patterns, HF model IDs)
               └──────┬───────┘
                      ▼
       ┌──────────────┼───────────────┬─────────────────┬───────────────┐
       ▼              ▼               ▼                 ▼               ▼
  ┌─────────┐  ┌──────────┐  ┌──────────────┐  ┌───────────┐  ┌──────────────┐
  │ AI-BOM  │  │ EU AI    │  │ ISO 27001 →  │  │ NIST AI   │  │ Annex IV     │
  │CDX+SPDX │  │ Act tier │  │ 42001 gaps   │  │ RMF cross │  │ docgen       │
  └─────────┘  └────┬─────┘  └──────────────┘  └───────────┘  └──────────────┘
                    │ (optional)
                    ▼
             LLM second opinion
             (Claude Haiku, never
              downgrades tier)
                    │
                    └───────────────────────────────────────────┐
                                                                ▼
                                                   compliance_report.html / .md
```

The accuracy lives in four editable YAML knowledge bases under `src/aibom_guard/data/`:

| File | Contents |
|------|----------|
| `ai_libraries.yaml` | 160+ AI library signatures (Python + JS) |
| `eu_ai_act.yaml` | Risk categories + keywords for all tiers |
| `iso_crosswalk.yaml` | Full ISO 27001 ↔ 42001 mapping (38 Annex A controls) |
| `nist_ai_rmf.yaml` | NIST AI RMF 1.0 — 65 subcategories with ISO 42001 crosswalks |

Improving coverage usually means editing YAML, not code.

---

## MCP server

Install the MCP server to call AIBOM-Guard directly from Claude Desktop or Cursor:

```bash
pip install "aibom-guard[mcp]"
```

Add to `~/.claude_desktop_config.json` (or equivalent):

```json
{
  "mcpServers": {
    "aibom-guard": {
      "command": "aibom-guard-mcp"
    }
  }
}
```

Available MCP tools: `scan`, `classify_risk`, `iso_gaps`, `nist_rmf`, `validate`, `full_report`.

---

## Optional dependencies

```bash
pip install "aibom-guard[validate]"   # full JSON Schema BOM validation
pip install "aibom-guard[llm]"        # LLM-assisted classification (Claude Haiku)
pip install "aibom-guard[mcp]"        # MCP server for Claude Desktop / Cursor
pip install "aibom-guard[all]"        # everything above
```

---

## Benchmark results

Five real open-source AI repos scanned — see [`docs/benchmarks.md`](docs/benchmarks.md).

| Repo | Tier | Components | HF models |
|------|------|-----------|-----------|
| openai/whisper | limited | 6 | 0 |
| microsoft/autogen | high* | 25 | 37 |
| roboflow/supervision | high* | 11 | 1 |
| guidance-ai/guidance | limited | 21 | 7 |
| Project-MONAI/MONAI | **HIGH** ✓ | 16 | 0 |

\* Tier after false-positive keyword fix (see benchmarks doc for methodology).
MONAI correctly triggers HIGH-RISK on the A3-medical Annex III category.

---

## Built to pair with Claude Code

This repo ships `.claude/skills/` (four custom skills) and a `compliance-reviewer`
subagent. Install [ECC](https://github.com/affaan-m/ECC) to get the full harness.

```bash
# Run AIBOM-Guard as MCP tools directly from Claude
aibom-guard-mcp

# Or drive the CLI from Claude Code
claude --dangerously-skip-permissions -p \
  'aibom-guard all . --name "MyApp" --use-case "hiring AI" --html -o reports/'
```

---

## Standards referenced

- Regulation (EU) 2024/1689 (EU AI Act) — Articles 5, 6, 11, 12, 50, 72; Annex III; Annex IV
- ISO/IEC 42001:2023 — AI management systems (full 38-control Annex A)
- ISO/IEC 27001:2022 — information security management (crosswalk baseline)
- NIST AI RMF 1.0 — GOVERN / MAP / MEASURE / MANAGE (65 subcategories)
- CycloneDX 1.6 — AI-BOM serialisation format
- SPDX 3.0 — AI Profile

---

## License

MIT — see [LICENSE](LICENSE).

---

*Triage aid only. Not legal advice. Confirm all findings with qualified human experts.*
