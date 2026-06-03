---
name: aibom-scan
description: Generate an AI Bill of Materials (AI-BOM) for a codebase. Use this skill whenever the user asks to inventory AI components, find what models/LLM APIs/ML libraries a project uses, produce an AI-BOM or ML-BOM, prepare AI supply-chain documentation, or assess a repo for the EU AI Act or ISO 42001 — even if they don't say "AI-BOM" explicitly. Trigger on phrases like "what AI is in this repo", "AI inventory", "scan for models", "AI supply chain", or any AI-governance/compliance scan request.
---

# AI-BOM Scan

Generate a CycloneDX-style AI Bill of Materials from a target project using the
`aibom-guard` CLI bundled in this repo.

## When to use
- The user wants an inventory of AI components (models, LLM APIs, ML frameworks, vector DBs, MCP tools).
- As the first step of any EU AI Act / ISO 42001 assessment (the AI-BOM feeds classification and docgen).

## Steps
1. Confirm the target path. Default to the current repo root if unspecified.
2. Run the scan and write machine-readable output:
   ```bash
   aibom-guard scan <TARGET> --name "<System Name>" -o reports/
   ```
   This writes `reports/aibom.cdx.json` (CycloneDX 1.6) and `reports/scan.json`.
3. Summarise findings for the user: number of components, by category, and any
   component whose `risk_note` mentions BIOMETRIC or external data egress.
4. If the user wants the full picture, hand off to the `eu-ai-act-classify` and
   `iso42001-crosswalk` skills, or run `aibom-guard all` (see below).

## One-shot full package
To produce the AI-BOM **plus** EU AI Act classification, ISO 42001 gap analysis,
Annex IV draft, and a Markdown report in one command:
```bash
aibom-guard all <TARGET> --name "<System Name>" --use-case "<what it does>" -o reports/
```

## Notes
- The scanner is offline and never executes target code.
- Detection coverage lives in `src/aibom_guard/data/ai_libraries.yaml`. If the user
  mentions a library that wasn't detected, add a signature there and re-scan.
- The AI-BOM is a starting artifact: model cards are emitted as empty stubs to be
  filled in. Validate against the official CycloneDX schema before auditor submission.
