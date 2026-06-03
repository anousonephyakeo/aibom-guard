# Architecture

AIBOM-Guard is a small, dependency-light pipeline. Each stage is a pure function over
the previous stage's output, which makes it easy to test and to call from an agent.

```
scan_project(target) -> ScanResult
    ├── build_aibom(scan)            -> CycloneDX dict   (aibom.py)
    ├── classify(scan, use_case)     -> ClassificationResult (classifier.py)
    ├── analyze_gaps(has_iso27001)   -> GapResult        (crosswalk.py)
    ├── generate_annex_iv(scan, cls) -> Markdown         (annex_iv.py)
    └── build_report(scan, cls, gaps)-> Markdown         (report.py)
```

## Modules
- **scanner.py** — walks the tree; parses requirements/pyproject/package.json against
  `data/ai_libraries.yaml`; detects model files by extension; greps source for API
  usage; builds a lowercase text corpus for the classifier. Never executes target code.
- **aibom.py** — emits CycloneDX 1.6 JSON; model artifacts/providers get model-card stubs.
- **classifier.py** — deterministic keyword match over the corpus + risk notes + an
  optional use-case string; highest-severity tier wins; "unclear" when AI is present
  but unmatched (never silently downgraded).
- **crosswalk.py** — walks `data/iso_crosswalk.yaml`; buckets controls into
  net-new / extend / covered; computes a readiness %.
- **annex_iv.py** / **report.py** — Markdown rendering.
- **cli.py** — argparse front-end: `scan`, `classify`, `crosswalk`, `docgen`, `all`.

## Extending
Most improvements are data, not code: edit the YAML files in `src/aibom_guard/data/`.
Add a test in `tests/test_pipeline.py` for every new detector or category.
