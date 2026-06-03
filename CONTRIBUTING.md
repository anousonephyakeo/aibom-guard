# Contributing to AIBOM-Guard

Contributions welcome. Most improvements are **YAML edits, not code changes** — extending the knowledge bases (AI library signatures, EU AI Act categories, ISO controls) is the highest-value contribution path.

## Development setup

```bash
git clone https://github.com/AnousonePhyakeo/aibom-guard.git
cd aibom-guard
pip install -e ".[dev]"
python -m pytest -q          # 42 tests must pass
```

## How to extend the knowledge bases

The four YAML files under `src/aibom_guard/data/` drive everything. No code changes needed for most additions.

### Add an AI library signature

Edit `src/aibom_guard/data/ai_libraries.yaml`:

```yaml
python:
  your-library-name:
    category: framework   # framework | model-provider | nlp | cv | vector-db | data | ...
    vendor: "Vendor Name"
    risk_note: "One-line note about risk relevance"
```

Then add a test in `tests/test_pipeline.py`:

```python
def test_detects_your_library():
    import tempfile
    from pathlib import Path
    from aibom_guard.scanner import scan_project
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "requirements.txt").write_text("your-library-name==1.0.0\n")
        s = scan_project(tmp)
        assert any(c.name == "your-library-name" for c in s.components)
```

### Add a new EU AI Act category or keyword

Edit `src/aibom_guard/data/eu_ai_act.yaml`. Add to the correct tier (`prohibited`, `high`, or `limited`):

```yaml
high:
  categories:
    - id: A3-your-category
      name: "Short descriptive name"
      keywords:
        - "specific phrase"
        - "another phrase"
```

**Important:** keywords must be specific enough that they don't match normal technical docstrings. Test for false positives before opening a PR.

### Add an ISO 42001 control mapping

Edit `src/aibom_guard/data/iso_crosswalk.yaml`.

### Add a NIST AI RMF subcategory

Edit `src/aibom_guard/data/nist_ai_rmf.yaml`.

## Code contributions

- Standard library + PyYAML only inside `src/aibom_guard/` — no new mandatory deps without discussion
- Optional extras (like `mcp`, `llm`, `validate`) are acceptable
- Every new detector or category must have a test in `tests/test_pipeline.py`
- Run lint: `ruff check src/`
- Run full pipeline smoke test before opening a PR:

```bash
aibom-guard all examples/sample-ai-app \
  --name "Demo" \
  --use-case "resume screening and candidate ranking" \
  --html -o /tmp/smoke-test/
```

Expected: `tier=high · components=9+`

## Pull request checklist

- [ ] `python -m pytest -q` passes (42+ tests)
- [ ] New functionality has a test in `tests/test_pipeline.py`
- [ ] `ruff check src/` passes
- [ ] For classifier changes: no new false positives on benign repos
- [ ] Legal disclaimers ("not legal advice") are untouched
- [ ] `CHANGELOG.md` updated with a bullet under the next version

## Guardrails (do not violate)

These match `CLAUDE.md`:

- Do not weaken or remove "not legal advice" / "triage aid" disclaimers from any user-facing output
- Do not add network calls to the core scanner — it must remain offline
- Do not add mandatory dependencies (optional extras are fine)
- Do not repurpose the scanner for surveillance, evasion, or other misuse

## Reporting issues

Use the [GitHub issue tracker](https://github.com/AnousonePhyakeo/aibom-guard/issues).  
Please use the structured issue templates — especially note if you're reporting a false positive in the EU AI Act tier.
