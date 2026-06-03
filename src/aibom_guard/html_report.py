"""Generate a self-contained HTML compliance report (Milestone 4).

All CSS is inlined — the output file has zero external dependencies and can be
opened directly from disk, emailed, or hosted on any static server.
"""
from __future__ import annotations

import html as _html
import datetime as _dt
from typing import TYPE_CHECKING

from . import __version__

if TYPE_CHECKING:
    from .scanner import ScanResult
    from .classifier import ClassificationResult
    from .crosswalk import GapResult

_TIER_COLOR = {
    "prohibited": "#c0392b",
    "high":       "#e74c3c",
    "limited":    "#f39c12",
    "minimal":    "#27ae60",
}
_TIER_LABEL = {
    "prohibited": "PROHIBITED",
    "high":       "HIGH RISK",
    "limited":    "LIMITED",
    "minimal":    "MINIMAL",
}
_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
     background:#f5f7fa;color:#2c3e50;line-height:1.6}
.wrap{max-width:980px;margin:0 auto;padding:24px}
header{background:#2c3e50;color:#fff;padding:22px 0;margin-bottom:24px}
header .wrap{display:flex;align-items:center;gap:18px}
.tier-badge{display:inline-block;padding:8px 22px;border-radius:6px;
            font-weight:700;font-size:13px;color:#fff;letter-spacing:.8px}
h1{font-size:21px;font-weight:700}
.sub{font-size:12px;opacity:.75;margin-top:3px}
.card{background:#fff;border-radius:8px;padding:22px;
      box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:20px}
.card h2{font-size:15px;color:#34495e;border-bottom:2px solid #ecf0f1;
          padding-bottom:9px;margin-bottom:15px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:14px}
.metric{text-align:center;padding:14px;background:#f8f9fa;border-radius:6px}
.mv{font-size:26px;font-weight:700;color:#2c3e50}
.ml{font-size:11px;color:#7f8c8d;margin-top:3px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#34495e;color:#fff;padding:9px 11px;text-align:left}
td{padding:8px 11px;border-bottom:1px solid #ecf0f1;vertical-align:top}
tr:nth-child(even) td{background:#f8f9fa}
.b{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;
   font-weight:600;text-transform:uppercase}
.b-high{background:#fdeceb;color:#c0392b}
.b-lim{background:#fef9ec;color:#d68910}
.b-pro{background:#c0392b;color:#fff}
.b-min{background:#eafaf1;color:#1e8449}
.b-lib{background:#eaecf4;color:#2c3e50}
.b-mod{background:#eaf4fc;color:#1a5276}
.b-api{background:#fdf2f8;color:#76448a}
.bar-wrap{height:30px;background:#ecf0f1;border-radius:6px;overflow:hidden;
          position:relative;margin:12px 0 6px}
.bar-fill{height:100%;display:flex;align-items:center;padding-left:11px;
          color:#fff;font-weight:600;font-size:13px;border-radius:6px}
.rat{font-size:13px;color:#555;background:#f8f9fa;padding:11px 15px;
     border-left:4px solid #3498db;border-radius:0 6px 6px 0;margin-bottom:14px}
.warn{background:#fef9ec;border-left:4px solid #f39c12;padding:11px 15px;
      border-radius:0 6px 6px 0;font-size:13px;margin-bottom:11px}
.err{background:#fdeceb;border-left:4px solid #e74c3c;padding:11px 15px;
     border-radius:0 6px 6px 0;font-size:13px;margin-bottom:11px}
.disc{font-size:11px;color:#7f8c8d;text-align:center;padding-top:14px;
      border-top:1px solid #ecf0f1;margin-top:22px}
code{background:#f0f0f0;padding:1px 4px;border-radius:3px;font-family:monospace}
ol{padding-left:20px;font-size:14px;line-height:2.1}
ul{padding-left:18px}
"""


def _e(s: object) -> str:
    return _html.escape(str(s))


def build_html_report(
    scan: "ScanResult",
    classification: "ClassificationResult",
    gaps: "GapResult",
    *,
    system_name: str = "AI System",
) -> str:
    """Return a fully self-contained HTML compliance report."""
    today = _dt.date.today().isoformat()
    tier = classification.tier
    tc = _TIER_COLOR.get(tier, "#7f8c8d")
    tl = _TIER_LABEL.get(tier, tier.upper())
    rp = gaps.readiness_pct
    bar_c = "#27ae60" if rp >= 70 else "#f39c12" if rp >= 40 else "#e74c3c"
    hf_ids = getattr(scan, "hf_model_ids", [])

    # --- Component rows ---
    comp_rows = ""
    for c in scan.components:
        kb = "b-mod" if c.kind == "model-file" else "b-api" if c.kind == "api-usage" else "b-lib"
        comp_rows += (
            f"<tr><td><code>{_e(c.name)}</code></td>"
            f"<td><span class='b {kb}'>{_e(c.kind)}</span></td>"
            f"<td>{_e(c.category)}</td><td>{_e(c.vendor or '—')}</td>"
            f"<td>{_e(c.version or '—')}</td>"
            f"<td style='font-size:12px'>{_e((c.risk_note or '—')[:80])}</td></tr>\n"
        )

    # --- Classification hit rows ---
    tier_cls = {"high": "b-high", "prohibited": "b-pro",
                "limited": "b-lim", "minimal": "b-min"}
    hit_rows = ""
    for h in classification.hits:
        tc2 = tier_cls.get(h.tier, "b-lib")
        hit_rows += (
            f"<tr><td><span class='b {tc2}'>{_e(h.tier)}</span></td>"
            f"<td><code>{_e(h.category_id)}</code></td>"
            f"<td>{_e(h.name)}</td>"
            f"<td style='font-size:12px'>{_e(', '.join(h.matched_keywords))}</td></tr>\n"
        )

    # --- Gap rows (net-new first, up to 25) ---
    gap_rows = ""
    for g in (gaps.net_new + gaps.extend)[:25]:
        gc = "b-high" if g.coverage == "none" else "b-lim"
        gl = "NET NEW" if g.coverage == "none" else "EXTEND"
        gap_rows += (
            f"<tr><td><code>{_e(g.id)}</code></td>"
            f"<td><span class='b {gc}'>{gl}</span></td>"
            f"<td>{_e(g.title)}</td>"
            f"<td style='font-size:12px'>{_e(g.gap[:130])}{'…' if len(g.gap)>130 else ''}</td></tr>\n"
        )

    # --- Warning banners ---
    banners = ""
    if classification.status == "unclear":
        banners += (
            "<div class='warn'>⚠️ <strong>Needs human review.</strong> "
            "AI detected but use case could not be classified automatically. "
            "Re-run with <code>--use-case</code>.</div>"
        )
    if tier in ("high", "prohibited"):
        banners += (
            f"<div class='err'>⚠️ <strong>{tl} risk detected.</strong> "
            "Triggers significant EU AI Act obligations. "
            "Escalate to compliance/legal before proceeding.</div>"
        )

    # --- HF model IDs block ---
    hf_block = ""
    if hf_ids:
        items = "".join(f"<li><code>{_e(mid)}</code></li>" for mid in hf_ids)
        hf_block = (
            f"<p style='margin-bottom:8px'><strong>Detected HuggingFace model IDs:</strong></p>"
            f"<ul style='margin-bottom:14px'>{items}</ul>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AIBOM-Guard — {_e(system_name)}</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <div class="wrap">
    <div>
      <h1>AIBOM-Guard Compliance Report</h1>
      <div class="sub">{_e(system_name)} &nbsp;·&nbsp; {today} &nbsp;·&nbsp; v{__version__}</div>
    </div>
    <div style="margin-left:auto">
      <span class="tier-badge" style="background:{tc}">{tl}</span>
    </div>
  </div>
</header>
<div class="wrap">

{banners}

<div class="card">
  <h2>Summary</h2>
  <div class="grid">
    <div class="metric">
      <div class="mv" style="color:{tc}">{tl}</div>
      <div class="ml">EU AI Act Tier (provisional)</div>
    </div>
    <div class="metric">
      <div class="mv">{len(scan.components)}</div>
      <div class="ml">AI Components</div>
    </div>
    <div class="metric">
      <div class="mv">{scan.files_scanned}</div>
      <div class="ml">Files Scanned</div>
    </div>
    <div class="metric">
      <div class="mv" style="color:{bar_c}">{rp}%</div>
      <div class="ml">ISO 42001 Readiness</div>
    </div>
    <div class="metric">
      <div class="mv">{len(gaps.net_new)}</div>
      <div class="ml">Net-New Controls</div>
    </div>
    <div class="metric">
      <div class="mv">{len(gaps.extend)}</div>
      <div class="ml">Controls to Extend</div>
    </div>
  </div>
  <div style="margin-top:18px">
    <div style="font-size:12px;color:#666;margin-bottom:5px">
      ISO 42001 Readiness &nbsp;—&nbsp; {rp}%
      &nbsp;({len(gaps.covered)} full &nbsp;·&nbsp; {len(gaps.extend)} partial
      &nbsp;·&nbsp; {len(gaps.net_new)} net-new)
    </div>
    <div class="bar-wrap">
      <div class="bar-fill" style="width:{rp}%;background:{bar_c}">{rp}%</div>
    </div>
  </div>
</div>

<div class="card">
  <h2>AI Bill of Materials</h2>
  {hf_block}
  <table>
    <thead><tr><th>Component</th><th>Kind</th><th>Category</th>
    <th>Vendor</th><th>Version</th><th>Risk Note</th></tr></thead>
    <tbody>
{comp_rows or "<tr><td colspan='6' style='color:#999;text-align:center'>No AI components detected.</td></tr>"}
    </tbody>
  </table>
</div>

<div class="card">
  <h2>EU AI Act Classification</h2>
  <div class="rat">{_e(classification.rationale)}</div>
  <table>
    <thead><tr><th>Tier</th><th>Category ID</th><th>Name</th><th>Matched Keywords</th></tr></thead>
    <tbody>
{hit_rows or "<tr><td colspan='4' style='color:#999;text-align:center'>No category keywords matched.</td></tr>"}
    </tbody>
  </table>
</div>

<div class="card">
  <h2>ISO 27001 → ISO 42001 Gap Analysis</h2>
  <p style="font-size:13px;color:#555;margin-bottom:14px">
    ISO 27001 held: <strong>{gaps.has_iso27001}</strong>
    &nbsp;·&nbsp; Total controls: <strong>{gaps.total_controls}</strong>
    &nbsp;·&nbsp; Net-new: <strong>{len(gaps.net_new)}</strong>
    &nbsp;·&nbsp; Extend: <strong>{len(gaps.extend)}</strong>
  </p>
  <table>
    <thead><tr><th>Control ID</th><th>Type</th><th>Title</th><th>Gap</th></tr></thead>
    <tbody>
{gap_rows or "<tr><td colspan='4' style='color:#999;text-align:center'>No gaps found.</td></tr>"}
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Recommended Next Actions</h2>
  <ol>
    <li>Validate the AI-BOM against the official CycloneDX schema and fill in model cards.</li>
    <li>Have a human confirm the EU AI Act tier — especially HIGH/PROHIBITED/unclear results.</li>
    <li>Address net-new ISO 42001 controls first: impact assessment, data provenance, AI documentation.</li>
    <li>Complete the generated Annex IV technical-documentation draft (<code>annex_iv.md</code>).</li>
    <li>Re-run this scan in CI so the AI-BOM and gap status stay current each release.</li>
  </ol>
</div>

<p class="disc">
  AIBOM-Guard v{__version__} &nbsp;·&nbsp; Generated {today} &nbsp;·&nbsp;
  This report is a triage aid. It does not constitute legal advice, a conformity assessment,
  or certification. Engage qualified compliance/legal experts for formal determinations.
</p>
</div>
</body>
</html>"""
