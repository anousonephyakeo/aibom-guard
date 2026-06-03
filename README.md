# AIBOM-Guard 🛡️

**Generate an AI Bill of Materials, triage your EU AI Act risk tier, and turn an
existing ISO 27001 ISMS into ISO 42001 readiness — from the command line, in seconds.**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)
[![CycloneDX](https://img.shields.io/badge/AI--BOM-CycloneDX%201.6-orange)](https://cyclonedx.org/)

> ⚖️ **AIBOM-Guard is a triage and documentation aid — not legal advice, an audit, or
> a conformity assessment.** Everything it outputs should be confirmed by a qualified
> human. High-risk and prohibited results must be escalated to compliance/legal.

---

## Why this exists

The EU AI Act's obligations for high-risk systems become enforceable on **2 August
2026**. Article 11 requires technical documentation, Article 12 requires event logging,
and ISO/IEC 42001 (the first AI management-system standard) is becoming the framework
organisations use to demonstrate it. Yet:

- Commercial AI-governance platforms cost tens of thousands per year.
- Fully automated AI-BOM generation didn't really exist in open source.
- Most teams that hold **ISO 27001** have no idea what **ISO 42001** adds on top.

AIBOM-Guard closes that gap for engineers: point it at a repo, get a machine-readable
AI inventory, a provisional risk tier, a prioritised ISO 42001 gap list, and a
pre-filled Annex IV technical-documentation draft.

## What it does

| Capability | Output |
|---|---|
| 🔎 **AI-BOM generation** | CycloneDX 1.6 JSON inventory of models, LLM APIs, ML frameworks, vector DBs, MCP tools, and model files |
| ⚖️ **EU AI Act triage** | Provisional tier (prohibited / high / limited / minimal) with the exact Annex III / Article 5 categories matched |
| 🧭 **ISO 27001 → 42001 gap analysis** | Net-new vs extend vs covered controls, plus a readiness % |
| 📄 **Annex IV docgen** | A structured technical-documentation draft, pre-filled and `[TODO]`-flagged |
| 🤖 **Overnight automation** | GitHub Action that scans nightly, uploads the package, and files an issue on high-risk findings |

## Quickstart

```bash
git clone https://github.com/anousonephyakeo/aibom-guard.git
cd aibom-guard
pip install -e ".[dev]"

# Run the whole pipeline on the bundled sample app
aibom-guard all examples/sample-ai-app \
  --name "Hiring Assistant" \
  --use-case "resume screening and candidate ranking for recruitment" \
  -o reports/
```

That writes a full compliance package to `reports/`:
`compliance_report.md`, `aibom.cdx.json`, `classification.json`,
`iso42001_gaps.json`, and `annex_iv.md`.

### Individual commands

```bash
aibom-guard scan      ./my-project -o reports/         # just the AI-BOM
aibom-guard classify  ./my-project --use-case "credit scoring"
aibom-guard crosswalk --no-iso27001                    # gap analysis
aibom-guard docgen    ./my-project --name "My System" -o reports/
aibom-guard all       ./my-project --fail-on-high      # CI gate: exit 2 if high-risk
```

## Sample output

Running against the bundled demo app (which screens resumes **and** does facial
recognition) correctly flags it as high-risk on two Annex III grounds:

```
| EU AI Act tier (provisional)        | 🔴 HIGH-RISK |
| AI components detected              | 10           |
| ISO 42001 readiness (vs ISO 27001)  | 35%          |
| ISO 42001 net-new controls          | 9            |

Matched categories:
- [high] A3-1-biometrics   — matched: biometric, facial recognition
- [high] A3-4-employment   — matched: resume screening, candidate ranking, ...
```

## How it works

```
                ┌─────────────┐
   target repo ─►   scanner   ├─► AIComponent[]  + use-case keywords
                └──────┬──────┘
                       ▼
        ┌──────────────┼───────────────┬────────────────┐
        ▼              ▼                ▼                ▼
   ┌─────────┐  ┌─────────────┐  ┌────────────┐  ┌──────────────┐
   │ AI-BOM  │  │ EU AI Act   │  │ ISO 27001→ │  │ Annex IV     │
   │ (CDX)   │  │ classifier  │  │ 42001 gaps │  │ docgen       │
   └─────────┘  └─────────────┘  └────────────┘  └──────────────┘
                       └──────────────┬────────────────┘
                                      ▼
                          compliance_report.md
```

The accuracy lives in three editable knowledge bases under
`src/aibom_guard/data/`: `ai_libraries.yaml` (detection signatures),
`eu_ai_act.yaml` (risk categories + keywords), and `iso_crosswalk.yaml`
(ISO 27001 ↔ 42001 mapping). Improving coverage usually means editing YAML, not code.

## Built to pair with Claude Code + ECC

This repo ships `.claude/skills/` (four custom skills), a `compliance-reviewer`
subagent, a `CLAUDE.md`/`AGENTS.md`, and a nightly GitHub Action — so you can drive
the whole thing from [Claude Code](https://www.anthropic.com/claude-code) and the
[ECC](https://github.com/affaan-m/ECC) harness. See `HANDOFF.md` for the roadmap.

## Standards referenced
- Regulation (EU) 2024/1689 (EU AI Act) — Articles 5, 6, 11, 12, 50, 72; Annex III; Annex IV
- ISO/IEC 42001:2023 — AI management systems
- ISO/IEC 27001:2022 — information security management
- CycloneDX 1.6 / ML-BOM — AI-BOM serialization format

## License
MIT — see [LICENSE](LICENSE).

---
*Triage aid only. Not legal advice. Confirm all findings with qualified experts.*
