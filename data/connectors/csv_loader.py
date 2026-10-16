"""Typed CSV loading for Growth OS sample data.

All tools read from precomputed CSVs under ``data/sample_data`` so the entire
pipeline runs with zero API keys. ``load_table`` keeps an in-process cache so
repeated tool calls do not re-parse files.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "sample_data"


def resolve_data_dir() -> Path:
    """Return the configured sample data directory (env override supported)."""
    override = os.getenv("GROWTH_OS_DATA_DIR")
    if override:
        return Path(override)
    return _DEFAULT_DATA_DIR


@lru_cache(maxsize=32)
def load_csv(filename: str) -> pd.DataFrame:
    """Load a CSV from the sample data directory, coercing numeric columns."""
    path = resolve_data_dir() / filename
    if not path.exists():
        raise FileNotFoundError(f"Sample data not found: {path}")
    df = pd.read_csv(path)
    for col in df.columns:
        coerced = pd.to_numeric(df[col], errors="coerce")
        df[col] = coerced.where(coerced.notna(), df[col])
    return df


def _native(value: Any) -> Any:
    """Coerce numpy scalars and non-strings to JSON-safe native types."""
    import numpy as np

    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def load_table(filename: str) -> list[dict[str, Any]]:
    """Return the CSV as a list of plain dicts (JSON-serializable)."""
    df = load_csv(filename)
    return [{k: _native(v) for k, v in row.items()} for row in df.to_dict(orient="records")]
