# CLAUDE.md — AIBOM-Guard

Context for Claude Code (and other harnesses) working in this repo. Read this first.

## What this project is
AIBOM-Guard is a **defensive AI-governance tool**. It scans a codebase, generates a
CycloneDX AI Bill of Materials, triages the EU AI Act risk tier, maps ISO 27001 →
ISO 42001 gaps, and drafts Annex IV technical documentation. It is a **triage and
documentation aid**, not legal advice, an audit, or a conformity assessment. Every
user-facing output must carry that caveat.

## Repo layout
- `src/aibom_guard/` — the engine (scanner, aibom, classifier, crosswalk, annex_iv, report, cli)
- `src/aibom_guard/data/*.yaml` — the knowledge bases (library signatures, EU AI Act categories, ISO crosswalk). **Most accuracy improvements happen by editing these.**
- `tests/` — pytest suite (run before every commit)
- `examples/sample-ai-app/` — a deliberately multi-risk app used by tests and demos
- `.claude/skills/` — custom skills for driving the CLI
- `.claude/agents/compliance-reviewer.md` — the review subagent
- `.github/workflows/nightly-compliance.yml` — overnight automation

## Build / test / run
```bash
pip install -e ".[dev]" --break-system-packages   # install (editable + dev)
python -m pytest -q                                # run tests (must pass)
aibom-guard all examples/sample-ai-app --name "Demo" --use-case "resume screening" -o reports/
```

## Conventions
- Standard library + PyYAML only for the core. Keep the engine dependency-light and **offline**; never execute target-project code.
- Every new detector/category needs a matching test in `tests/test_pipeline.py`.
- Run the full test suite and a sample `aibom-guard all` before committing.
- Keep `SKILL.md` descriptions specific and slightly "pushy" so they trigger reliably.

## Guardrails (do not violate)
- Do NOT auto-`git push`, open public PRs, or publish packages without explicit human approval.
- Do NOT present any classification as a legal determination; always recommend human/legal review for HIGH/PROHIBITED/unclear results.
- Do NOT weaken or remove the "not legal advice" disclaimers.
- This is governance tooling only — never repurpose the scanner to build surveillance, evasion, or other misuse.

## Where to go next
See `HANDOFF.md` for the prioritised roadmap of what to build next.
