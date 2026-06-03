# AIBOM-Guard

**Generate an AI Bill of Materials, triage your EU AI Act risk tier, and turn an
existing ISO 27001 ISMS into ISO 42001 readiness — from the command line, in seconds.**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-42%20passing-brightgreen)](tests/)
[![CycloneDX](https://img.shields.io/badge/AI--BOM-CycloneDX%201.6-orange)](https://cyclonedx.org/)
[![SPDX](https://img.shields.io/badge/AI--BOM-SPDX%203.0-blue)](https://spdx.dev/)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-blue)](https://AnousonePhyakeo.github.io/aibom-guard)

> ⚖️ **AIBOM-Guard is a triage and documentation aid — not legal advice, an audit, or
> a conformity assessment.** All output should be confirmed by a qualified human.
> High-risk and prohibited results must be escalated to compliance/legal.

---

## Table of Contents

- [Why this exists](#why-this-exists)
- [What it does](#what-it-does)
- [Dashboard screenshot](#dashboard-screenshot)
- [Quickstart](#quickstart)
- [Commands](#commands)
- [Sample output](#sample-output)
- [How it works](#how-it-works)
- [MCP server](#mcp-server)
- [Optional dependencies](#optional-dependencies)
- [Benchmark results](#benchmark-results)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Standards referenced](#standards-referenced)
- [License](#license)

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
| 🔎 **AI component scan** | Detects 220+ AI libraries, model files, and API usage patterns across Python/JS |
| 📦 **AI-BOM generation** | CycloneDX 1.6 JSON **and** SPDX 3.0 AI Profile — both validated |
| ⚖️ **EU AI Act triage** | Provisional tier (prohibited / high / limited / minimal) with matched Annex III / Article 5 categories |
| 🧭 **ISO 42001 gap analysis** | Net-new vs extend vs covered controls; readiness % vs ISO 27001 baseline |
| 🗺️ **NIST AI RMF crosswalk** | Full 65-subcategory GOVERN/MAP/MEASURE/MANAGE framework with ISO 42001 crosswalks |
| 📄 **Annex IV docgen** | Structured technical-documentation draft, pre-filled and `[TODO]`-flagged |
| 🌐 **HTML dashboard** | Self-contained, shareable compliance report — no server, no external dependencies |
| 🧠 **LLM-assisted classification** | Optional Claude Haiku second opinion; never downgrades a rule-based tier |
| 🔌 **Evidence collectors** | Read-only GitHub repo + HuggingFace Hub metadata → mapped to ISO 42001 controls |
| 🤖 **MCP server** | Wrap the CLI as MCP tools for Claude Desktop, Cursor, or any MCP-compatible agent |

---

## Dashboard screenshot

![AIBOM-Guard compliance dashboard — HIGH RISK tier with summary metrics, AI component table, and ISO 42001 gap analysis](docs/assets/screenshot-dashboard.png)

*The `--html` flag generates a self-contained dashboard. Open directly from disk — no server or internet connection required.*

---

## Quickstart

### Install

```bash
pip install aibom-guard
```

Or from source (editable + dev extras):

```bash
git clone https://github.com/AnousonePhyakeo/aibom-guard.git
cd aibom-guard
pip install -e ".[dev]"
python -m pytest -q   # 42 tests — all should pass
```

### Run — full compliance package

```bash
aibom-guard all ./my-ai-project \
  --name "My System" \
  --use-case "describe what the system does in plain language" \
  --html \
  -o reports/
```

One command generates **8 output files** in `reports/`:

| File | Contents |
|------|----------|
| `compliance_report.html` | Interactive compliance dashboard (open in browser) |
| `compliance_report.md` | Same report in Markdown (CI-friendly) |
| `aibom.cdx.json` | CycloneDX 1.6 AI-BOM |
| `aibom.spdx.json` | SPDX 3.0 AI-BOM |
| `classification.json` | EU AI Act tier + matched categories |
| `iso42001_gaps.json` | ISO 42001 control gap analysis |
| `annex_iv.md` | EU AI Act Annex IV technical documentation draft |
| `validation.txt` | CycloneDX schema validation result |

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
  --validate       # exit non-zero if BOM has schema errors
  -o reports/
```

### `scan` — AI component detection only

```bash
aibom-guard scan ./project
aibom-guard scan ./project --format spdx    # SPDX 3.0 output
aibom-guard scan ./project --validate       # validate emitted BOM
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
aibom-guard collect ./project --github myorg/my-repo -o reports/
```

---

## Sample output

Running against the bundled demo app (resume screening + facial recognition) correctly
flags it as high-risk on two Annex III grounds:

```
EU AI Act tier (provisional)       🔴 HIGH-RISK
AI components detected             9
ISO 42001 readiness (vs 27001)     35%
ISO 42001 net-new controls         13

Matched categories:
  [high]    A3-1-biometrics  — biometric, facial recognition, face-recognition
  [high]    A3-4-employment  — resume screening, candidate ranking, hiring
  [limited] T1-chatbot       — openai, anthropic
```

> For the full visual dashboard see the [screenshot above](#dashboard-screenshot) or run with `--html`.

---

## How it works

```
               ┌──────────────┐
  target repo ─►    scanner   ├─► AIComponent[]  (220+ sigs, 14 API patterns, HF model IDs)
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

Accuracy lives in four editable YAML knowledge bases under `src/aibom_guard/data/`:

| File | Contents |
|------|----------|
| `ai_libraries.yaml` | 220+ AI library signatures (Python + JS) |
| `eu_ai_act.yaml` | 21 risk categories + keywords for all tiers |
| `iso_crosswalk.yaml` | ISO 27001 ↔ 42001 mapping (42 controls) |
| `nist_ai_rmf.yaml` | NIST AI RMF 1.0 — subcategories with ISO 42001 crosswalks |

Improving coverage usually means **editing YAML, not code**.

---

## MCP server

Use AIBOM-Guard as tools directly from Claude Desktop or Cursor:

```bash
pip install "aibom-guard[mcp]"
```

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "aibom-guard": {
      "command": "aibom-guard-mcp"
    }
  }
}
```

Available tools: `scan`, `classify_risk`, `iso_gaps`, `nist_rmf`, `validate`, `full_report`.  
→ [Full MCP setup guide](https://AnousonePhyakeo.github.io/aibom-guard/mcp-server/)

---

## Optional dependencies

```bash
pip install "aibom-guard[validate]"   # full JSON Schema BOM validation (requires network)
pip install "aibom-guard[llm]"        # LLM-assisted classification (Claude Haiku)
pip install "aibom-guard[mcp]"        # MCP server for Claude Desktop / Cursor
pip install "aibom-guard[all]"        # everything above
```

→ [Full optional dependencies guide](https://AnousonePhyakeo.github.io/aibom-guard/optional-deps/)

---

## Benchmark results

Five real open-source AI repos scanned — full methodology and per-repo analysis: [docs/benchmarks.md](docs/benchmarks.md).

| Repo | Tier | Components | HF models |
|------|------|-----------|-----------|
| openai/whisper | limited | 6 | 0 |
| microsoft/autogen | high | 25 | 37 |
| roboflow/supervision | high | 11 | 1 |
| guidance-ai/guidance | limited | 21 | 7 |
| Project-MONAI/MONAI | **HIGH** ✓ | 16 | 0 |

MONAI correctly triggers HIGH-RISK on the `A3-medical` Annex III category ("medical imaging", "clinical decision").

---

## Documentation

Full documentation: **<https://AnousonePhyakeo.github.io/aibom-guard>**

| Page | Contents |
|------|----------|
| [Quickstart](https://AnousonePhyakeo.github.io/aibom-guard/quickstart/) | Install, first run, output files explained |
| [Commands](https://AnousonePhyakeo.github.io/aibom-guard/commands/) | Full CLI reference for all 6 subcommands |
| [Architecture](https://AnousonePhyakeo.github.io/aibom-guard/architecture/) | Pipeline stages, module responsibilities |
| [Benchmarks](https://AnousonePhyakeo.github.io/aibom-guard/benchmarks/) | Detection accuracy on 5 real AI repos |
| [Example compliance report](https://AnousonePhyakeo.github.io/aibom-guard/examples/compliance-report/) | See what a full report looks like |
| [Example Annex IV](https://AnousonePhyakeo.github.io/aibom-guard/examples/annex-iv/) | See what the generated technical doc looks like |
| [Contributing](CONTRIBUTING.md) | How to contribute — mostly YAML edits |
| [Changelog](CHANGELOG.md) | Version history |

---

## Contributing

Contributions welcome. Most improvements are YAML edits — adding AI library signatures,
EU AI Act keywords, or ISO 42001 control mappings. No deep code knowledge required.

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, conventions, and the PR checklist.

---

## Standards referenced

- Regulation (EU) 2024/1689 (EU AI Act) — Articles 5, 6, 11, 12, 50, 72; Annex III; Annex IV
- ISO/IEC 42001:2023 — AI management systems (full 42-control Annex A)
- ISO/IEC 27001:2022 — information security management (crosswalk baseline)
- NIST AI RMF 1.0 — GOVERN / MAP / MEASURE / MANAGE (65 subcategories)
- CycloneDX 1.6 — AI-BOM serialisation format
- SPDX 3.0 — AI Profile

---

## License

MIT — see [LICENSE](LICENSE).

---

*Triage aid only. Not legal advice. Confirm all findings with qualified human experts.*
