"""AIBOM-Guard: AI Bill of Materials + EU AI Act / ISO 42001 compliance triage.

A defensive compliance tool that scans a codebase for AI components, generates a
CycloneDX or SPDX AI-BOM, suggests an EU AI Act risk tier, maps ISO 27001 → ISO 42001
gaps, crosswalks to the NIST AI RMF, and drafts Annex IV technical documentation.

This is a triage and documentation aid, not legal advice or an audit substitute.
"""

__version__ = "0.2.0"

from .scanner import scan_project, AIComponent, ScanResult
from .aibom import build_aibom, build_spdx
from .classifier import classify, ClassificationResult
from .crosswalk import analyze_gaps, analyze_nist, GapResult, NistResult
from .annex_iv import generate_annex_iv
from .report import build_report
from .validate import validate_bom, format_report
from .html_report import build_html_report

__all__ = [
    "__version__",
    "scan_project",
    "AIComponent",
    "ScanResult",
    "build_aibom",
    "build_spdx",
    "classify",
    "ClassificationResult",
    "analyze_gaps",
    "analyze_nist",
    "GapResult",
    "NistResult",
    "generate_annex_iv",
    "build_report",
    "validate_bom",
    "format_report",
    "build_html_report",
]
