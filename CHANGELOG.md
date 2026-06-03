# Changelog

All notable changes are documented here.  
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) · Versioning: [Semantic Versioning](https://semver.org/).

---

## [0.2.0] — 2026-06-03

### Added
- CycloneDX 1.6 BOM schema validation (`aibom-guard validate`, `--validate` flag)
- SPDX 3.0 AI-BOM output (`--format spdx`)
- HuggingFace model ID extraction from `from_pretrained()` and `owner/model` kwargs
- Self-contained HTML compliance dashboard (`--html`)
- ISO 42001 full 38-control Annex A crosswalk (`aibom-guard crosswalk`)
- NIST AI RMF 1.0 crosswalk (`--framework nist`)
- LLM-assisted second-opinion classification via Claude Haiku (`--llm`; requires `ANTHROPIC_API_KEY`)
- GitHub evidence collector (`--github owner/repo`)
- HuggingFace Hub evidence collector
- MCP server wrapper exposing 6 tools (`aibom-guard-mcp`)
- 160+ AI library signatures (up from 60 in v0.1.0)
- New EU AI Act categories: `A3-medical`, `A3-safety-components`, `T4-emotion-categorisation`
- Full CI pipeline (Python 3.11 + 3.12, lint, BOM schema validation, nightly self-scan)
- Nightly compliance workflow with automatic GitHub issue creation on HIGH/PROHIBITED findings
- GitHub Actions SHA-pinned for supply chain security (OWASP A08)
- Input validation on GitHub and HuggingFace collectors (OWASP A03)

### Fixed
- False positive: `manipulat` keyword no longer triggers `P2-manipulative` for "data manipulation" / "image manipulation" docstrings
- False positive: Anthropic API model names (e.g. `claude-3-5-sonnet`) no longer appear in `hf_model_ids`
- Monorepo deduplication: library beats api-usage for the same package name in CycloneDX output

### Changed
- Expanded EU AI Act keyword sets across all 21 categories for higher recall
- `P2-manipulative` keywords replaced with specific harm phrases (precision improvement)

---

## [0.1.0] — 2026-06-03

### Added
- Initial release
- AI component scanner: 60 Python library signatures, 14 API/SDK usage patterns, model file detection
- CycloneDX 1.5 AI-BOM generation
- EU AI Act risk tier classification (prohibited / high / limited / minimal)
- ISO 27001 → ISO 42001 gap analysis (42 controls)
- EU AI Act Annex IV technical documentation draft
- Markdown compliance report
- CLI: `scan`, `classify`, `bom`, `crosswalk`, `annex-iv`, `all`
