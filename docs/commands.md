# Command Reference

All commands share the same entry point: `aibom-guard <subcommand> [options]`.

---

## `all` — full compliance package

Run the complete pipeline in one command.

```bash
aibom-guard all <path> [options]
```

| Option | Description |
|--------|-------------|
| `--name TEXT` | System name for the report header |
| `--use-case TEXT` | Plain-language description of what the system does (improves classifier) |
| `--html` | Also generate `compliance_report.html` dashboard |
| `--format cdx\|spdx\|both` | BOM output format (default: `both`) |
| `--framework nist` | Include NIST AI RMF crosswalk |
| `--llm` | Second-opinion tier via Claude Haiku (requires `ANTHROPIC_API_KEY`) |
| `--iso27001 / --no-iso27001` | Assume ISO 27001 held when computing gap % (default: true) |
| `--validate` | Run CycloneDX schema validation (requires `pip install aibom-guard[validate]`) |
| `-o, --output-dir DIR` | Directory to write all output files (default: current dir) |

**Output files:** `compliance_report.md`, `compliance_report.html` (with `--html`), `aibom.cdx.json`, `aibom.spdx.json`, `classification.json`, `iso42001_gaps.json`, `annex_iv.md`, `validation.txt`

---

## `scan` — AI component scanner

Scan a project and print the CycloneDX BOM to stdout.

```bash
aibom-guard scan <path>
```

Detects:
- Dependencies in `requirements*.txt`, `pyproject.toml`, `package.json` matched against 220+ Python and 34 JS AI library signatures
- Model artifact files (`.onnx`, `.pt`, `.pkl`, `.safetensors`, and 17 more extensions)
- AI API/SDK usage patterns in `.py`, `.js`, `.ts`, `.ipynb` source files
- HuggingFace model IDs from `from_pretrained()` and `owner/model` kwargs

---

## `classify` — EU AI Act risk classifier

```bash
aibom-guard classify <path> [--use-case TEXT] [--llm]
```

Outputs JSON with `tier`, `confidence`, `hits` (matched category IDs and keywords).

Tiers: `prohibited` → `high` → `limited` → `minimal`

The `--use-case` description is appended to the text corpus before keyword matching — providing it significantly improves accuracy.

With `--llm`: runs a Claude Haiku second-opinion pass. The LLM can only upgrade the tier (conservative merge rule), never downgrade it.

---

## `bom` — build AI Bill of Materials

```bash
aibom-guard bom <path> [--name TEXT] [--format cdx|spdx|both] [-o DIR]
```

Writes `aibom.cdx.json` (CycloneDX 1.6) and/or `aibom.spdx.json` (SPDX 3.0 AI Profile).

---

## `crosswalk` — compliance framework gap analysis

```bash
aibom-guard crosswalk [--iso27001] [--framework nist] [-o DIR]
```

| Option | Output |
|--------|--------|
| `--iso27001` | ISO 27001 → ISO 42001 gap analysis: 42 controls, net-new vs extend, readiness % |
| `--framework nist` | NIST AI RMF 1.0: GOVERN / MAP / MEASURE / MANAGE subcategories |

Both options can be combined. Output: `iso42001_gaps.json` and/or `nist_rmf.json`.

---

## `annex-iv` — EU AI Act Annex IV documentation draft

```bash
aibom-guard annex-iv <path> [--name TEXT] [--use-case TEXT] [-o DIR]
```

Drafts a structured Annex IV technical documentation file (`annex_iv.md`) covering intended purpose, performance metrics, data governance, human oversight, and risk management sections.

---

## `validate` — CycloneDX BOM validation

```bash
aibom-guard validate <bom.json>
```

Validates a CycloneDX JSON file against the structural requirements of the CycloneDX 1.6 specification.

With `pip install aibom-guard[validate]` and network access: additionally validates against the official CycloneDX 1.6 JSON schema.
