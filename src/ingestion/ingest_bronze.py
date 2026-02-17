"""Resolve source path for Bronze: input file at project root (e.g. tickets_raw.json)."""

from __future__ import annotations

from pathlib import Path

from src.utils.config import INPUT_PATH


def get_source_path() -> Path:
    """
    Return the path to the source input file for the Bronze layer.
    Raises FileNotFoundError if the input file is missing.
    """
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Place tickets_raw.json at the project root or set INPUT_FILENAME in .env."
        )
    return INPUT_PATH
