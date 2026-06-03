# Optional Dependencies

The core engine requires only `PyYAML`. Everything else is opt-in.

```bash
# Minimal — scan + classify + BOM + crosswalk + report
pip install aibom-guard

# CycloneDX JSON schema validation
pip install "aibom-guard[validate]"

# LLM-assisted classification (requires ANTHROPIC_API_KEY)
pip install "aibom-guard[llm]"

# MCP server for Claude Desktop / Cursor
pip install "aibom-guard[mcp]"

# MkDocs documentation (for contributors)
pip install "aibom-guard[docs]"

# All optional extras
pip install "aibom-guard[all]"

# Development (tests, lint, all extras)
pip install "aibom-guard[dev]"
```

| Extra | Packages added | Purpose |
|-------|---------------|---------|
| `validate` | `jsonschema>=4.21` | Full CycloneDX 1.6 JSON schema validation (needs network) |
| `llm` | `anthropic>=0.25` | Claude Haiku second-opinion pass on risk tier |
| `mcp` | `mcp>=1.0` | MCP server — expose tools to Claude Desktop / Cursor |
| `docs` | `mkdocs-material>=9.5` | Build the documentation site locally |
| `all` | all three above | Everything except docs and dev |
| `dev` | pytest, ruff, all | Full development environment |

## Using the LLM classifier

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
aibom-guard all ./my-project --use-case "hiring platform" --llm -o reports/
```

The LLM is used for a second-opinion pass only. It can raise the tier (conservative merge rule) but never lower it below the keyword-based result. The classification is always labelled "triage aid — confirm with a human."
