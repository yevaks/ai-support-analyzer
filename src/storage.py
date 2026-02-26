"""Simple JSON read/write helpers."""

from __future__ import annotations

import json
from pathlib import Path


def load_json(path: str) -> list[dict]:
    """Load a JSON array from a file. Returns an empty list if the file is missing."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    with p.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}, got {type(data).__name__}")
    return data


def save_json(data: list[dict], path: str) -> None:
    """Serialise a list of dicts to a JSON file with pretty formatting."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} record(s) → {p.resolve()}")
