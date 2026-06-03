"""Consolidate all analyses into a single human-readable compliance report."""
from __future__ import annotations

import datetime as _dt
from typing import TYPE_CHECKING

from . import __version__

if TYPE_CHECKING:
    from .scanner import ScanResult
    from .classifier import ClassificationResult
    from .crosswalk import GapResult

_TIER_BADGE = {
    "prohibited": "⛔ PROHIBITED",
    "high": "🔴 HIGH-RISK",
    "limited": "🟡 LIMITED (transparency)",
    "minimal": "🟢 MINIMAL",
}


def build_report(scan: "ScanResult", classification: "ClassificationResult",
                 gaps: "GapResult", *, system_name: str = "AI System") -> str:
    """Return a Markdown compliance summary report."""
    today = _dt.date.today().isoformat()
    badge = _TIER_BADGE.get(classification.tier, classification.tier)

    # Component summary by category
    by_cat: dict[str, int] = {}
    for c in scan.components:
        by_cat[c.category] = by_cat.get(c.category, 0) + 1
    cat_lines = "\n".join(f"- **{k}**: {v}" for k, v in sorted(by_cat.items())) or "- _none_"

    # Top gaps (net-new first)
    net_new_lines = "\n".join(
        f"- `{g.id}` **{g.title}** — {g.gap}" for g in gaps.net_new[:12]
    ) or "- _none_"
    extend_lines = "\n".join(
        f"- `{g.id}` **{g.title}** (extends {g.iso27001_ref or '—'}) — {g.gap}"
        for g in gaps.extend[:12]
    ) or "- _none_"

    hits_lines = "\n".join(
        f"- [{h.tier}] `{h.category_id}` {h.name} — matched: {', '.join(h.matched_keywords)}"
        for h in classification.hits
    ) or "- _no category keywords matched_"

    review_flag = ""
    if classification.status == "unclear":
        review_flag = (
            "\n> ⚠️ **Needs human review.** AI components were found but the use case "
            "could not be classified automatically. Re-run with `--use-case` describing "
            "what the system does.\n"
        )
    if classification.tier in ("high", "prohibited"):
        review_flag += (
            f"\n> ⚠️ **{badge}.** This triggers significant EU AI Act obligations "
            "(or a ban). Escalate to compliance/legal before proceeding.\n"
        )

    return f"""# AIBOM-Guard Compliance Report — {system_name}

_Generated {today} · AIBOM-Guard v{__version__} · triage aid, not legal advice_

## Summary

| Metric | Value |
|---|---|
| EU AI Act tier (provisional) | {badge} |
| Classification status | {classification.status} ({classification.confidence} confidence) |
| AI components detected | {len(scan.components)} |
| Files scanned | {scan.files_scanned} |
| ISO 42001 readiness (vs ISO 27001) | **{gaps.readiness_pct}%** |
| ISO 42001 net-new controls | {len(gaps.net_new)} |
| ISO 42001 controls to extend | {len(gaps.extend)} |
{review_flag}
## 1. AI Bill of Materials (summary)

Components by category:

{cat_lines}

> Full machine-readable AI-BOM is emitted separately as CycloneDX JSON (`aibom.cdx.json`).

## 2. EU AI Act classification

**Provisional tier: {badge}**

{classification.rationale}

Matched categories:

{hits_lines}

## 3. ISO 27001 → ISO 42001 gap analysis

Assuming ISO 27001 held: **{gaps.has_iso27001}** · Readiness: **{gaps.readiness_pct}%**

### Net-new controls (no ISO 27001 equivalent — start here)

{net_new_lines}

### Controls to extend (ISO 27001 foundation exists, AI-specific work needed)

{extend_lines}

## 4. Recommended next actions

1. Validate the AI-BOM against the official CycloneDX schema and fill in model cards.
2. Have a human confirm the EU AI Act tier — especially anything marked HIGH/PROHIBITED/unclear.
3. Work the net-new ISO 42001 controls first (impact assessment, data provenance, AI documentation).
4. Complete the generated Annex IV technical-documentation draft (`annex_iv.md`).
5. Re-run this scan in CI so the AI-BOM and gap status stay current each release.

---
_AIBOM-Guard performs automated triage. It does not constitute legal advice, a
conformity assessment, or certification. Engage qualified compliance/legal experts._
"""
