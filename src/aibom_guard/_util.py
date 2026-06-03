"""Internal helpers shared across modules."""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

DATA_DIR = Path(__file__).parent / "data"


@functools.lru_cache(maxsize=None)
def load_data(filename: str) -> dict[str, Any]:
    """Load and cache a bundled YAML data file from the package data directory."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Bundled data file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def normalize_pkg(name: str) -> str:
    """Normalize a dependency name for matching (lowercase, strip extras/quotes)."""
    name = name.strip().strip('"').strip("'").lower()
    # strip version specifiers and extras: "torch[cuda]>=2.0" -> "torch"
    for sep in ("[", ">", "<", "=", "~", "!", " ", ";", "@"):
        if sep in name:
            name = name.split(sep, 1)[0]
    return name.strip()
