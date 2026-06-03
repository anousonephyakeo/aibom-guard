# Architecture

AIBOM-Guard is a small, dependency-light pipeline. Each stage is a pure function over
the previous stage's output, which makes it easy to test and to call from an agent.

## Pipeline

```
aibom-guard all <target>
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  scanner.py — scan_project(target) → ScanResult             │
│                                                             │
│  • Walks every file in the target directory                 │
│  • requirements*.txt / pyproject.toml / package.json        │
│    → matched against ai_libraries.yaml (220 Python, 34 JS) │
│  • Source files (.py .js .ts .ipynb)                        │
│    → 14 AI API/SDK usage patterns                           │
│    → HuggingFace model IDs from from_pretrained()           │
│  • File extensions (.onnx .pt .pkl .safetensors ...)        │
│    → 21 model artifact types                                │
│  Never executes target code. Offline by design.             │
└──────────────────────────┬──────────────────────────────────┘
                           │ ScanResult
          ┌────────────────┼────────────────────┐
          ▼                ▼                    ▼
   aibom.py          classifier.py         crosswalk.py
   build_aibom()     classify()            analyze_gaps()
   CycloneDX 1.6     EU AI Act tier        ISO 27001→42001
   SPDX 3.0          prohibited/high/      42 controls
                     limited/minimal       readiness %
          │                │                    │
          └────────────────┼────────────────────┘
                           ▼
                    annex_iv.py + report.py
                    Annex IV draft + compliance_report.md/.html
```

## Function signatures

```
scan_project(target) -> ScanResult
    ├── build_aibom(scan)            -> CycloneDX dict   (aibom.py)
    ├── classify(scan, use_case)     -> ClassificationResult (classifier.py)
    ├── analyze_gaps(has_iso27001)   -> GapResult        (crosswalk.py)
    ├── generate_annex_iv(scan, cls) -> Markdown         (annex_iv.py)
    └── build_report(scan, cls, gaps)-> Markdown         (report.py)
```

## Modules

| Module | Responsibility |
|--------|---------------|
| `scanner.py` | Walks the file tree; parses manifests; detects model files, API usage, HF model IDs; builds text corpus. Never executes target code. |
| `aibom.py` | Emits CycloneDX 1.6 JSON + SPDX 3.0 AI Profile. Model artifacts/providers get model-card stubs. Deduplicates on name (library beats api-usage). |
| `classifier.py` | Deterministic keyword match over corpus + risk notes + use-case string. Highest-severity tier wins. Optional LLM second-opinion via `--llm` (can only raise tier). |
| `crosswalk.py` | Maps ISO 27001 → ISO 42001 (42 controls: net-new / extend / covered). Also emits NIST AI RMF 1.0 subcategories. |
| `annex_iv.py` | Drafts EU AI Act Annex IV technical documentation in Markdown. |
| `report.py` | Renders the Markdown compliance report. |
| `html_report.py` | Renders the self-contained HTML dashboard (no external deps). |
| `validate.py` | Structural CycloneDX 1.6 validation; optional full JSON schema validation. |
| `cli.py` | argparse entry point: `scan`, `classify`, `bom`, `crosswalk`, `annex-iv`, `validate`, `all`. |
| `mcp_server.py` | FastMCP server wrapping all 6 tools for Claude Desktop / Cursor. |
| `collectors/` | Optional evidence collectors: GitHub repo metadata, HuggingFace Hub model cards. |

## Extending
Most improvements are data, not code: edit the YAML files in `src/aibom_guard/data/`.
Add a test in `tests/test_pipeline.py` for every new detector or category.
