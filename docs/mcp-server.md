# MCP Server

AIBOM-Guard ships an [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that exposes the compliance pipeline as tools for Claude Desktop, Cursor, or any MCP-compatible client.

## Install

```bash
pip install "aibom-guard[mcp]"
```

## Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "aibom-guard": {
      "command": "aibom-guard-mcp"
    }
  }
}
```

Restart Claude Desktop. You will see AIBOM-Guard tools available.

## Available tools

| Tool | Description |
|------|-------------|
| `scan` | Scan a project path and return the AI component list |
| `classify_risk` | Classify EU AI Act risk tier for a project |
| `iso_gaps` | Get ISO 27001 → ISO 42001 gap analysis |
| `nist_rmf` | Get NIST AI RMF crosswalk |
| `validate` | Validate a CycloneDX BOM JSON string |
| `full_report` | Run the complete pipeline and return the Markdown compliance report |

## Example prompts (in Claude Desktop)

> "Scan my project at /Users/me/my-ai-app and tell me its EU AI Act risk tier."

> "Run a full compliance report on /Users/me/hiring-system with use case 'resume screening'."

> "Validate this CycloneDX BOM: { ... }"
