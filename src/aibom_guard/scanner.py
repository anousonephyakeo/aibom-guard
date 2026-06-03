"""Scan a project directory for AI components.

Detection sources:
  1. Dependency manifests (requirements*.txt, pyproject.toml, package.json) matched
     against the curated signature list in data/ai_libraries.yaml.
  2. Serialized model artifacts on disk (by file extension).
  3. AI API/SDK usage in source files (lightweight keyword scan), used both as
     evidence and to feed the EU AI Act classifier.

The scanner is intentionally dependency-light and offline. It does not execute any
code from the target project.
"""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from ._util import load_data, normalize_pkg

# Directories we never descend into.
_SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "venv", ".venv", "env",
    "__pycache__", ".mypy_cache", ".pytest_cache", "dist", "build",
    ".tox", ".idea", ".vscode", "site-packages",
}

_SOURCE_SUFFIXES = {".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".ipynb"}
_DOC_SUFFIXES = {".md", ".rst", ".txt"}

# Regexes that catch the most common ways an AI service is invoked in source.
# (name, compiled pattern)
_USAGE_PATTERNS = [
    ("openai", re.compile(r"\bopenai\b|OpenAI\(", re.I)),
    ("anthropic", re.compile(r"\banthropic\b|Anthropic\(", re.I)),
    ("huggingface", re.compile(r"from_pretrained\(|huggingface", re.I)),
    ("langchain", re.compile(r"\blangchain\b", re.I)),
    ("mcp", re.compile(r"modelcontextprotocol|\bmcp\b", re.I)),
    ("bedrock", re.compile(r"bedrock-runtime|invoke_model", re.I)),
    ("transformers-pipeline", re.compile(r"\bpipeline\(\s*[\"']", re.I)),
    ("litellm", re.compile(r"\blitellm\b", re.I)),
    ("vllm", re.compile(r"\bvllm\b|from vllm", re.I)),
    ("ollama", re.compile(r"\bollama\b", re.I)),
    ("vertexai", re.compile(r"vertexai|aiplatform|VertexAI\(", re.I)),
    ("azure-openai", re.compile(r"AzureOpenAI\(|azure\.ai\.", re.I)),
    ("cohere", re.compile(r"\bcohere\b|Cohere\(", re.I)),
    ("together", re.compile(r"\btogether\b|TogetherAI\(", re.I)),
]

# Extracts HuggingFace model IDs from source code.
#
# Two separate patterns to avoid false positives:
#   1. from_pretrained("anything")  — always HuggingFace, capture everything
#   2. model="owner/model"          — only capture if it contains "/" (owner/model
#      format); bare names like "claude-3-5-sonnet" or "gpt-4" are API model
#      names from Anthropic/OpenAI, not HF model IDs.
_HF_PRETRAINED_RE = re.compile(
    r'from_pretrained\s*\(\s*["\']([A-Za-z0-9][A-Za-z0-9_\-./]{2,79})["\']'
)
_HF_MODEL_KWARG_RE = re.compile(
    r'\bmodel\s*=\s*["\']([A-Za-z0-9][A-Za-z0-9_\-]{0,63}/[A-Za-z0-9][A-Za-z0-9_\-./]{0,63})["\']'
)
_HF_MODEL_SKIP = frozenset({
    "cpu", "cuda", "auto", "true", "false", "utf-8", "utf8",
    "json", "text", "rb", "wb", "r", "w", "a",
})


@dataclass
class AIComponent:
    """A single detected AI component."""
    name: str
    kind: str                       # library | model-file | api-usage
    category: str = "unknown"       # framework | model-provider | ...
    vendor: str | None = None
    version: str | None = None
    risk_note: str | None = None
    evidence: str = ""              # where it was found

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "category": self.category,
            "vendor": self.vendor,
            "version": self.version,
            "risk_note": self.risk_note,
            "evidence": self.evidence,
        }


@dataclass
class ScanResult:
    target: str
    components: list[AIComponent] = field(default_factory=list)
    keywords_found: set[str] = field(default_factory=set)   # use-case keywords for classifier
    text_corpus: str = ""                                   # concatenated doc/source text (truncated)
    files_scanned: int = 0
    hf_model_ids: list[str] = field(default_factory=list)  # HF model IDs detected in source

    @property
    def has_ai(self) -> bool:
        return len(self.components) > 0

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "files_scanned": self.files_scanned,
            "has_ai": self.has_ai,
            "components": [c.to_dict() for c in self.components],
            "keywords_found": sorted(self.keywords_found),
            "hf_model_ids": self.hf_model_ids,
        }


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        yield path


def _parse_requirements(text: str) -> list[tuple[str, str | None]]:
    out = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        version = None
        m = re.search(r"[=<>~!]=?\s*([0-9][\w.\-]*)", line)
        if m:
            version = m.group(1)
        out.append((normalize_pkg(line), version))
    return out


def _parse_pyproject(text: str) -> list[tuple[str, str | None]]:
    out: list[tuple[str, str | None]] = []
    try:
        data = tomllib.loads(text)
    except Exception:
        return out
    # PEP 621
    for dep in data.get("project", {}).get("dependencies", []) or []:
        out.append((normalize_pkg(dep), None))
    for group in (data.get("project", {}).get("optional-dependencies", {}) or {}).values():
        for dep in group:
            out.append((normalize_pkg(dep), None))
    # Poetry
    poetry = data.get("tool", {}).get("poetry", {})
    for name in (poetry.get("dependencies", {}) or {}):
        if name.lower() != "python":
            out.append((normalize_pkg(name), None))
    return out


def _parse_package_json(text: str) -> list[tuple[str, str | None]]:
    import json
    out: list[tuple[str, str | None]] = []
    try:
        data = json.loads(text)
    except Exception:
        return out
    for key in ("dependencies", "devDependencies"):
        for name, ver in (data.get(key, {}) or {}).items():
            out.append((name.strip().lower(), str(ver).lstrip("^~") or None))
    return out


def scan_project(target: str | Path, max_corpus_chars: int = 200_000) -> ScanResult:
    """Scan ``target`` directory and return a :class:`ScanResult`."""
    root = Path(target).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Target path does not exist: {root}")

    sigs = load_data("ai_libraries.yaml")
    py_sigs = {normalize_pkg(k): v for k, v in (sigs.get("python") or {}).items()}
    js_sigs = {k.strip().lower(): v for k, v in (sigs.get("javascript") or {}).items()}
    model_exts = {e["ext"]: e["type"] for e in sigs.get("model_file_extensions", [])}

    result = ScanResult(target=str(root))
    seen: set[tuple[str, str]] = set()    # (name, kind) de-dup
    seen_hf: set[str] = set()
    corpus_parts: list[str] = []
    corpus_len = 0

    for path in _iter_files(root):
        name = path.name.lower()
        suffix = path.suffix.lower()

        # 1) model artifacts on disk
        if suffix in model_exts:
            key = (path.name, "model-file")
            if key not in seen:
                seen.add(key)
                result.components.append(AIComponent(
                    name=path.name, kind="model-file", category="model-artifact",
                    risk_note=model_exts[suffix],
                    evidence=str(path.relative_to(root)),
                ))
            continue

        # 2) dependency manifests
        deps: list[tuple[str, str | None]] = []
        sig_table = None
        if name.startswith("requirements") and suffix == ".txt":
            deps = _parse_requirements(_safe_read(path)); sig_table = py_sigs
        elif name == "pyproject.toml":
            deps = _parse_pyproject(_safe_read(path)); sig_table = py_sigs
        elif name == "package.json":
            deps = _parse_package_json(_safe_read(path)); sig_table = js_sigs

        if sig_table is not None:
            for dep_name, version in deps:
                meta = sig_table.get(dep_name)
                if not meta:
                    continue
                key = (dep_name, "library")
                if key in seen:
                    continue
                seen.add(key)
                result.components.append(AIComponent(
                    name=dep_name, kind="library",
                    category=meta.get("category", "unknown"),
                    vendor=meta.get("vendor"), version=version,
                    risk_note=meta.get("risk_note"),
                    evidence=str(path.relative_to(root)),
                ))
            # manifests aren't added to the keyword corpus
            continue

        # 3) source / docs -> usage patterns + keyword corpus + HF model IDs
        if suffix in _SOURCE_SUFFIXES or suffix in _DOC_SUFFIXES:
            text = _safe_read(path)
            if not text:
                continue
            result.files_scanned += 1
            for label, pat in _USAGE_PATTERNS:
                if pat.search(text):
                    key = (label, "api-usage")
                    if key not in seen:
                        seen.add(key)
                        result.components.append(AIComponent(
                            name=label, kind="api-usage", category="usage",
                            evidence=str(path.relative_to(root)),
                        ))
            # Extract HuggingFace model IDs from source code.
            if suffix in _SOURCE_SUFFIXES:
                for pat in (_HF_PRETRAINED_RE, _HF_MODEL_KWARG_RE):
                    for m in pat.finditer(text):
                        mid = m.group(1)
                        if mid.lower() not in _HF_MODEL_SKIP and mid not in seen_hf:
                            seen_hf.add(mid)
                            result.hf_model_ids.append(mid)
            if corpus_len < max_corpus_chars:
                snippet = text[: max_corpus_chars - corpus_len]
                corpus_parts.append(snippet.lower())
                corpus_len += len(snippet)

    result.text_corpus = "\n".join(corpus_parts)
    return result


def _safe_read(path: Path, limit: int = 1_000_000) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            return fh.read(limit)
    except (OSError, UnicodeError):
        return ""
