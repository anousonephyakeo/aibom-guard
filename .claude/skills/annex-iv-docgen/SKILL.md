---
name: annex-iv-docgen
description: Draft EU AI Act Annex IV technical documentation for a high-risk AI system. Use whenever the user needs Article 11 technical documentation, an Annex IV technical file, model cards, a conformity-assessment documentation pack, or "technical documentation for the AI Act". Trigger on "Annex IV", "Article 11", "technical documentation", "technical file", "model card", "conformity assessment docs", even without exact wording.
---

# Annex IV Technical Documentation Draft

Produce a structured Annex IV technical-documentation skeleton, pre-filled from the
AI-BOM and classification, with `[TODO]` markers where human input is required.

## Steps
1. Ensure a scan + classification exist (run `aibom-scan` and `eu-ai-act-classify`).
2. Generate the draft:
   ```bash
   aibom-guard docgen <TARGET> --use-case "<what it does>" --name "<System Name>" -o reports/
   ```
   Writes `reports/annex_iv.md`.
3. Walk the user through the `[TODO]` sections and offer to help fill them — especially:
   - intended purpose & provider/deployer roles (§1)
   - data datasheets & provenance (§2.5)
   - human oversight measures (§2.6, §3.3)
   - validation/testing metrics incl. fairness (§2.8)
   - event logging & retention ≥ 6 months (§8.2)
4. Keep Appendix A (component inventory) in sync with the AI-BOM each release.

## Important
The output is a scaffold to accelerate documentation, mapped to Annex IV of
Regulation (EU) 2024/1689. It is not a completed technical file and not legal advice.
