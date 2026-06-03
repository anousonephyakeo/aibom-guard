"""Suggest an EU AI Act risk tier for the scanned system.

Approach (deterministic, explainable):
  * Search the scan's text corpus + component risk notes + an optional user-supplied
    use-case description for category keywords from data/eu_ai_act.yaml.
  * Highest-severity match wins: prohibited > high > limited > minimal.
  * If AI is present but nothing matches, fall back to the configured default
    (``limited``) and mark confidence low / status "unclear" so a human reviews it.

This deliberately errs toward surfacing things for review (the documented "40%
unclear" problem) rather than silently downgrading risk.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ._util import load_data

_TIER_ORDER = {"minimal": 0, "limited": 1, "high": 2, "prohibited": 3}


@dataclass
class CategoryHit:
    tier: str
    category_id: str
    name: str
    matched_keywords: list[str]


@dataclass
class ClassificationResult:
    tier: str
    status: str                       # "matched" | "unclear" | "no-ai"
    confidence: str                   # "low" | "medium" | "high"
    hits: list[CategoryHit] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "status": self.status,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "hits": [
                {
                    "tier": h.tier,
                    "category_id": h.category_id,
                    "name": h.name,
                    "matched_keywords": h.matched_keywords,
                }
                for h in self.hits
            ],
        }


def _search(text: str, keywords: list[str]) -> list[str]:
    return [kw for kw in keywords if kw.lower() in text]


def classify(scan, use_case: str | None = None) -> ClassificationResult:
    """Classify a :class:`ScanResult`. ``use_case`` is an optional free-text
    description of what the system does (greatly improves accuracy)."""
    cfg = load_data("eu_ai_act.yaml")

    # Build the haystack: corpus + risk notes + names + use-case description.
    parts = [getattr(scan, "text_corpus", "") or ""]
    for c in getattr(scan, "components", []):
        parts.append((c.risk_note or "").lower())
        parts.append((c.name or "").lower())
    if use_case:
        parts.append(use_case.lower())
    haystack = "\n".join(parts)

    if not getattr(scan, "has_ai", False) and not use_case:
        return ClassificationResult(
            tier="minimal", status="no-ai", confidence="high",
            rationale="No AI components or use-case signals detected.",
        )

    hits: list[CategoryHit] = []
    for tier in ("prohibited", "high", "limited"):
        for cat in (cfg.get(tier, {}).get("categories") or []):
            matched = _search(haystack, cat.get("keywords", []))
            if matched:
                hits.append(CategoryHit(tier, cat["id"], cat["name"], matched))

    if not hits:
        default_tier = cfg.get("default_when_ai_present_but_unclassified", "limited")
        return ClassificationResult(
            tier=default_tier, status="unclear", confidence="low",
            rationale=(
                "AI components detected but no use-case category matched. "
                "Defaulted to '%s' pending human review. Provide a --use-case "
                "description to improve classification." % default_tier
            ),
        )

    # Highest severity tier present wins.
    top_tier = max((h.tier for h in hits), key=lambda t: _TIER_ORDER[t])
    top_hits = [h for h in hits if h.tier == top_tier]
    confidence = "high" if len(top_hits) >= 2 or top_tier == "prohibited" else "medium"
    names = "; ".join(sorted({h.name for h in top_hits}))
    rationale = (
        f"Classified '{top_tier}' from {len(top_hits)} matching "
        f"{'practice' if top_tier == 'prohibited' else 'use-case'} "
        f"categor{'y' if len(top_hits) == 1 else 'ies'}: {names}. "
        "Confirm with a human before relying on this."
    )
    return ClassificationResult(
        tier=top_tier, status="matched", confidence=confidence,
        hits=hits, rationale=rationale,
    )
