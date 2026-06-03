# AGENTS.md

Cross-harness context (Codex, Cursor, OpenCode, Gemini, etc.). See CLAUDE.md for the
full version; this is the portable summary.

AIBOM-Guard is a defensive AI-governance CLI: AI-BOM generation + EU AI Act risk
triage + ISO 27001→42001 gap analysis + Annex IV docgen. Triage aid only, not legal
advice.

Build/test:
  pip install -e ".[dev]" --break-system-packages
  python -m pytest -q

Run:
  aibom-guard all <target> --name "<name>" --use-case "<desc>" -o reports/

Rules: stdlib+PyYAML core, offline, never execute target code, every detector needs a
test, never present classifications as legal determinations, never remove disclaimers,
never auto-push or publish without human approval.
