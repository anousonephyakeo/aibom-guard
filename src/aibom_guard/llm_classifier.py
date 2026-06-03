"""Optional LLM-assisted EU AI Act classification using the Anthropic API.

Gate: only activates when ``ANTHROPIC_API_KEY`` is set in the environment
      AND the ``anthropic`` package is installed (pip install aibom-guard[llm]).

Conservative merge rule: the LLM result can NEVER downgrade the tier below
the rule-based result. If the LLM suggests a lower tier, the rule-based tier
is kept and the discrepancy is noted in the rationale. This prevents an LLM
from inadvertently underclassifying a high-risk system.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .scanner import ScanResult
    from .classifier import ClassificationResult

_TIER_ORDER = {"minimal": 0, "limited": 1, "high": 2, "prohibited": 3}
_VALID_TIERS = frozenset({"prohibited", "high", "limited", "minimal"})

_SYSTEM_PROMPT = (
    "You are an EU AI Act compliance expert helping to classify AI systems. "
    "Your role is to assist human reviewers — you are NOT making legal determinations. "
    "Always be conservative: when in doubt, classify at the higher risk tier."
)

_USER_TEMPLATE = """Analyze this AI system and suggest an EU AI Act risk tier.

## AI components detected
{components}

## Use case description
{use_case}

## Rule-based classification result
Tier: {rule_tier} (confidence: {rule_confidence})
Rationale: {rule_rationale}

## Your task
Review the components and use case. Consider:
- Article 5 (prohibited practices): social scoring, manipulative AI, real-time biometric in public spaces
- Annex III (high-risk): biometrics, critical infrastructure, education, employment, essential services, law enforcement, migration, justice
- Article 50 (limited): chatbots, generative AI, recommender systems
- Minimal: everything else

Respond with EXACTLY this format (no other text):
TIER: <one of: prohibited | high | limited | minimal>
JUSTIFICATION: <one sentence explaining why, referencing the specific category>
UNCERTAINTY: <low | medium | high>
"""


def llm_classify(
    scan: "ScanResult",
    rule_result: "ClassificationResult",
    *,
    use_case: str | None = None,
    model: str = "claude-haiku-4-5-20251001",
) -> "ClassificationResult":
    """Run LLM-assisted classification and merge with rule-based result.

    Returns the rule_result unchanged if ANTHROPIC_API_KEY is not set or
    if the anthropic package is not installed.
    """
    from .classifier import ClassificationResult

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return rule_result

    try:
        import anthropic  # type: ignore[import]
    except ImportError:
        return rule_result

    components_str = "\n".join(
        f"- {c.name} ({c.kind}/{c.category})"
        + (f" — {c.risk_note}" if c.risk_note else "")
        for c in scan.components
    ) or "No components detected"

    user_msg = _USER_TEMPLATE.format(
        components=components_str,
        use_case=use_case or "Not provided",
        rule_tier=rule_result.tier,
        rule_confidence=rule_result.confidence,
        rule_rationale=rule_result.rationale,
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=300,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = message.content[0].text.strip()
    except Exception as exc:
        # LLM call failed — fall back to rule-based
        rule_result.rationale += f" [LLM call failed: {exc}]"
        return rule_result

    llm_tier, justification, uncertainty = _parse_response(text)

    if not llm_tier:
        rule_result.rationale += " [LLM response unparseable; using rule-based result]"
        return rule_result

    # Conservative merge: never let LLM downgrade below rule-based tier
    rule_order = _TIER_ORDER.get(rule_result.tier, 0)
    llm_order = _TIER_ORDER.get(llm_tier, 0)

    if llm_order < rule_order:
        final_tier = rule_result.tier
        note = (
            f"LLM suggested '{llm_tier}' but rule-based result '{rule_result.tier}' "
            "was kept (conservative merge — never downgrade)."
        )
    elif llm_order > rule_order:
        final_tier = llm_tier
        note = f"LLM upgraded tier from '{rule_result.tier}' to '{llm_tier}'."
    else:
        final_tier = rule_result.tier
        note = f"LLM agreed with rule-based tier '{final_tier}'."

    combined_rationale = (
        f"[LLM-assisted] {note} "
        f"LLM justification: {justification} "
        f"(uncertainty: {uncertainty}). "
        f"Rule-based: {rule_result.rationale}"
    )

    return ClassificationResult(
        tier=final_tier,
        status="llm-assisted",
        confidence="medium" if uncertainty == "high" else rule_result.confidence,
        hits=rule_result.hits,
        rationale=combined_rationale,
    )


def _parse_response(text: str) -> tuple[str | None, str, str]:
    """Parse the structured LLM response. Returns (tier, justification, uncertainty)."""
    tier = None
    justification = "No justification provided"
    uncertainty = "medium"

    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("TIER:"):
            raw = line.split(":", 1)[1].strip().lower()
            if raw in _VALID_TIERS:
                tier = raw
        elif line.upper().startswith("JUSTIFICATION:"):
            justification = line.split(":", 1)[1].strip()
        elif line.upper().startswith("UNCERTAINTY:"):
            raw_u = line.split(":", 1)[1].strip().lower()
            if raw_u in ("low", "medium", "high"):
                uncertainty = raw_u

    return tier, justification, uncertainty
