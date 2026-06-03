"""ISO 27001 -> ISO 42001 gap analysis + NIST AI RMF crosswalk.

Supports two frameworks:
  iso42001  - ISO/IEC 42001:2023 Annex A (full 38-control set)
  nist      - NIST AI RMF 1.0 (GOVERN / MAP / MEASURE / MANAGE)

Given the set of ISO 27001 Annex A controls an organisation has implemented
(or the assumption it holds full ISO 27001 certification), report which
ISO 42001 Annex A controls are net-new ("none") or require AI-specific
extension ("partial"). For NIST, reports all subcategories with their
ISO 42001 crosswalk for additional context.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ._util import load_data


@dataclass
class ControlGap:
    id: str
    title: str
    objective: str
    coverage: str            # full | partial | none
    iso27001_ref: str | None
    gap: str


@dataclass
class GapResult:
    has_iso27001: bool
    total_controls: int
    net_new: list[ControlGap] = field(default_factory=list)
    extend: list[ControlGap] = field(default_factory=list)
    covered: list[ControlGap] = field(default_factory=list)

    @property
    def readiness_pct(self) -> int:
        if self.total_controls == 0:
            return 0
        score = len(self.covered) + 0.5 * len(self.extend)
        return round(100 * score / self.total_controls)

    def to_dict(self) -> dict:
        def ser(items):
            return [c.__dict__ for c in items]
        return {
            "has_iso27001": self.has_iso27001,
            "total_controls": self.total_controls,
            "readiness_pct": self.readiness_pct,
            "net_new_count": len(self.net_new),
            "extend_count": len(self.extend),
            "covered_count": len(self.covered),
            "net_new": ser(self.net_new),
            "extend": ser(self.extend),
            "covered": ser(self.covered),
        }


@dataclass
class NistCategory:
    function_id: str
    function_name: str
    category_id: str
    category_name: str
    subcategory_id: str
    subcategory_title: str
    description: str
    iso42001_crosswalk: list[str]


@dataclass
class NistResult:
    total_subcategories: int
    functions: dict[str, list[NistCategory]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        out: dict = {
            "framework": "NIST AI RMF 1.0",
            "total_subcategories": self.total_subcategories,
            "functions": {},
        }
        for fn_id, subs in self.functions.items():
            out["functions"][fn_id] = [
                {
                    "subcategory_id": s.subcategory_id,
                    "category": s.category_name,
                    "title": s.subcategory_title,
                    "description": s.description,
                    "iso42001_crosswalk": s.iso42001_crosswalk,
                }
                for s in subs
            ]
        return out


def analyze_gaps(
    has_iso27001: bool = True,
    implemented_27001: set[str] | None = None,
) -> GapResult:
    """Analyze ISO 42001 gaps relative to ISO 27001 baseline."""
    cfg = load_data("iso_crosswalk.yaml")
    controls = cfg.get("iso42001_controls", [])

    result = GapResult(has_iso27001=has_iso27001, total_controls=len(controls))

    for c in controls:
        coverage = c.get("coverage", "none")
        ref = c.get("iso27001_ref")

        if not has_iso27001:
            coverage = "none" if coverage != "full" else "partial"
        elif implemented_27001 is not None and coverage in ("full", "partial") and ref:
            ref_id = ref.split()[0]  # "A.5.1 Policies..." -> "A.5.1"
            if ref_id not in implemented_27001:
                coverage = "none"

        gap = ControlGap(
            id=c["id"], title=c["title"], objective=c.get("objective", ""),
            coverage=coverage, iso27001_ref=ref, gap=c.get("gap", ""),
        )
        if coverage == "none":
            result.net_new.append(gap)
        elif coverage == "partial":
            result.extend.append(gap)
        else:
            result.covered.append(gap)

    return result


def analyze_nist() -> NistResult:
    """Return the full NIST AI RMF 1.0 subcategory list with ISO 42001 crosswalk."""
    cfg = load_data("nist_ai_rmf.yaml")
    functions_data = cfg.get("functions", [])

    result = NistResult(total_subcategories=0)

    for fn in functions_data:
        fn_id = fn["id"]
        fn_name = fn["name"]
        cats: list[NistCategory] = []

        for cat in fn.get("categories", []):
            for sub in cat.get("subcategories", []):
                nc = NistCategory(
                    function_id=fn_id,
                    function_name=fn_name,
                    category_id=cat["id"],
                    category_name=cat["name"],
                    subcategory_id=sub["id"],
                    subcategory_title=sub["title"],
                    description=sub.get("description", "").strip(),
                    iso42001_crosswalk=sub.get("iso42001_crosswalk", []),
                )
                cats.append(nc)
                result.total_subcategories += 1

        result.functions[fn_id] = cats

    return result
