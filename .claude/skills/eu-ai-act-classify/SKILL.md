---
name: eu-ai-act-classify
description: Triage a software system's EU AI Act risk tier (prohibited / high-risk / limited / minimal). Use whenever the user asks whether a system is high-risk, which EU AI Act category it falls under, whether Annex III applies, what obligations they face under the AI Act, or asks to assess regulatory risk of an AI feature. Trigger on "EU AI Act", "high-risk AI", "Annex III", "AI Act classification", "is this regulated", even without the exact wording.
---

# EU AI Act Risk Classification

Suggest a provisional EU AI Act risk tier for a scanned system. This is a **triage
aid**, never a legal determination — always tell the user to confirm with a human,
and escalate anything that lands on HIGH or PROHIBITED.

## Steps
1. Make sure a scan exists (run the `aibom-scan` skill first if not).
2. Get a use-case description from the user — one sentence on what the system does.
   This dramatically improves accuracy. If they can't give one, run without it and
   expect an "unclear" result that needs review.
3. Classify:
   ```bash
   aibom-guard classify <TARGET> --use-case "<what the system does>"
   ```
4. Report the tier, the matched Annex III / Article 5 categories, and confidence.

## Interpreting results
- `prohibited` — Article 5 banned practice. Stop and escalate immediately.
- `high` — Annex III high-risk. Full Chapter III obligations (risk mgmt, data
  governance, technical docs, logging, human oversight, conformity assessment).
  Offer to run `annex-iv-docgen` next.
- `limited` — transparency obligations only (Article 50): disclose AI interaction,
  label synthetic content.
- `minimal` — no specific obligations.
- status `unclear` — AI present but use case unmatched; **must** be reviewed by a human.

## Important
- Enforcement of high-risk obligations applies from 2 August 2026 — flag timelines.
- The keyword knowledge base is `src/aibom_guard/data/eu_ai_act.yaml`; refine it if
  the user's domain has terms it misses.
- Never downgrade a tier to be reassuring. When in doubt, surface for review.
