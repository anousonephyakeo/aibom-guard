# Quickstart

## Install

```bash
pip install aibom-guard
```

Or install from source (editable + dev extras):

```bash
git clone https://github.com/AnousonePhyakeo/aibom-guard.git
cd aibom-guard
pip install -e ".[dev]"
python -m pytest -q   # verify: 42 tests pass
```

---

## Run — full compliance package

```bash
aibom-guard all ./my-ai-project \
  --name "My System" \
  --use-case "describe what the system does in plain language" \
  --html \
  -o reports/
```

One command generates **8 output files**:

| File | Contents |
|------|---------|
| `compliance_report.html` | Interactive dashboard — tier badge, metrics, tables |
| `compliance_report.md` | Same report in Markdown (CI-friendly) |
| `aibom.cdx.json` | CycloneDX 1.6 AI Bill of Materials |
| `aibom.spdx.json` | SPDX 3.0 AI Profile |
| `classification.json` | EU AI Act tier + matched categories |
| `iso42001_gaps.json` | ISO 42001 control gap analysis |
| `annex_iv.md` | EU AI Act Annex IV technical documentation draft |
| `validation.txt` | CycloneDX schema validation result |

---

## Example — scan the included demo app

The repo ships with a deliberately multi-risk demo app (hiring assistant with face recognition):

```bash
aibom-guard all examples/sample-ai-app \
  --name "Hiring Assistant" \
  --use-case "resume screening and candidate ranking with biometric face recognition" \
  --html -o reports/
```

Expected output:

```
[all] tier=high (matched) · components=9 · ISO42001 readiness=35% · HF models=0
✓ aibom.cdx.json is structurally valid (CycloneDX 1.6).
```

Open `reports/compliance_report.html` in a browser to see the full dashboard.

---

## Individual commands

Run just one step if you don't need the full package:

```bash
# Scan only — print CycloneDX BOM JSON
aibom-guard scan ./my-project

# Classify only — print EU AI Act tier
aibom-guard classify ./my-project --use-case "what it does"

# Build BOM — write aibom.cdx.json and aibom.spdx.json
aibom-guard bom ./my-project --name "My App" -o reports/

# ISO crosswalk — gap analysis assuming ISO 27001 held
aibom-guard crosswalk --iso27001

# NIST AI RMF crosswalk
aibom-guard crosswalk --framework nist

# Validate an existing CycloneDX BOM
aibom-guard validate reports/aibom.cdx.json
```

→ [Full command reference](commands.md)
