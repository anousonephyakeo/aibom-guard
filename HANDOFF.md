# HANDOFF.md — roadmap for Claude Code

This is the prioritised build plan. Hand this repo to Claude Code (with ECC installed)
and point it at this file. Each milestone is independently shippable, has a clear
"definition of done," and respects the guardrails in `CLAUDE.md`.

**Working agreement for the agent**
- After each milestone: run `python -m pytest -q` and a sample `aibom-guard all`; both must pass.
- Commit per milestone with a conventional-commit message. **Do not `git push` or open public PRs without explicit human approval.**
- Add/extend tests for every new detector, category, or command.
- Never weaken disclaimers or present classifications as legal determinations.

---

## ✅ Milestone 0 — Foundation (DONE)
The working v0.1 you're starting from: scanner, AI-BOM, EU AI Act classifier, ISO
crosswalk, Annex IV docgen, report, CLI, 13 passing tests, sample app, ECC skills +
agent, nightly workflow. Verify with `pip install -e ".[dev]" && pytest -q`.

## Milestone 1 — Schema validation & richer AI-BOM  *(highest value, low risk)*
**Goal:** make the AI-BOM auditor-grade.
- Add `cyclonedx-python-lib` (optional dep) and validate emitted BOMs against the
  official CycloneDX 1.6 JSON schema; add a `--validate` flag to `scan`/`all`.
- Populate model cards from `transformers`/Hugging Face references found in source
  (model IDs, task) instead of empty stubs.
- Add SPDX 3.0 AI-BOM as an alternative output format (`--format spdx`).
- **Done when:** emitted BOMs validate clean and a model ID detected in code appears in the BOM. Tests cover both.

## Milestone 2 — Deepen the knowledge bases  *(accuracy)*
**Goal:** higher detection and classification recall.
- Expand `data/ai_libraries.yaml` (aim for 150+ signatures incl. audio/vision/RAG).
- Expand `data/eu_ai_act.yaml` keyword sets; add a small synonym layer.
- Complete `data/iso_crosswalk.yaml` to the full ISO 42001 Annex A control set.
- Add a `data/nist_ai_rmf.yaml` and a `crosswalk --framework nist` option.
- **Done when:** scanning 3–5 real open-source AI repos yields sensible BOMs; document results in `docs/benchmarks.md`.

## Milestone 3 — LLM-assisted classification (optional, gated)
**Goal:** resolve the "unclear" cases with an LLM second opinion.
- Add a pluggable classifier backend: when `ANTHROPIC_API_KEY` (or Claude Code) is
  available, send the use-case + matched evidence to a model and ask for a tier with
  a justification, then **merge conservatively** with the rule-based result (take the
  higher severity; never let the LLM downgrade below a keyword match).
- Keep the rule-based path the default so the tool stays offline-capable.
- **Done when:** `classify --llm` improves an "unclear" sample to a justified tier, with the rule-based result still shown.

## Milestone 4 — HTML report + dashboard
**Goal:** a shareable, non-technical-friendly artifact.
- Render `compliance_report.md` to a self-contained HTML (use the ECC `frontend-design`
  skill / `frontend-slides` patterns). Include the tier badge, gap chart, and BOM table.
- Add `aibom-guard report --html`.
- **Done when:** `reports/compliance_report.html` opens standalone and looks polished.

## Milestone 5 — Evidence collectors (connect to real infra)  *(stretch)*
**Goal:** move from code-scan to live evidence (the perennial compliance pain point).
- Add read-only collectors that map findings to ISO 42001 controls: GitHub settings
  (branch protection, SAST enabled), and a cloud model-registry reader (Hugging Face
  Hub / SageMaker / Azure ML) to enrich the AI-BOM.
- Strictly read-only; credentials via env vars; never write to the target systems.
- **Done when:** a collector attaches at least one piece of live evidence to a control in the report.

## Milestone 6 — Packaging & distribution
**Goal:** make it trivially installable and a strong GitHub showcase.
- GitHub Action for CI (lint + test on push); badge in README.
- Publish to PyPI (`pip install aibom-guard`) and add a `pipx` one-liner — **only with human approval** for the actual publish step.
- Optional: wrap the CLI as an MCP server so any MCP-compatible agent can call
  `scan`/`classify`/`crosswalk` as tools.
- **Done when:** CI is green on push and install instructions are verified from a clean environment.

---

## Useful external repos to pair with (for the agent to reference)
- **ECC** (`affaan-m/ECC`) — the harness: skills, the `security-review`/`code-reviewer`
  agents, the `frontend-design` skill for Milestone 4, and AgentShield for self-scanning this repo's own config.
- **CycloneDX** tooling (`CycloneDX/cyclonedx-python-lib`) — schema validation for Milestone 1.
- **cdxgen** (`CycloneDX/cdxgen`) — mature BOM generator; reference for broader ecosystem detection.
- **CISO Assistant** / **Probo (getprobo/probo)** — open-source GRC platforms; study their
  control models and MCP tool surface if you extend toward full ISMS features (but
  don't reimplement them — AIBOM-Guard's edge is AI-native + AI Act + dev-first).

## Definition of "end product" for v1.0
A `pip install`-able tool with: validated CycloneDX + SPDX AI-BOM output, full ISO
42001 Annex A crosswalk, NIST AI RMF support, optional LLM-assisted classification, a
polished HTML report, green CI, an MCP server wrapper, and docs. All disclaimers intact.
