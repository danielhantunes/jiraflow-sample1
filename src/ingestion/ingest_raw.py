"""Ingest raw ticket data from the local tickets_raw.json file into the Raw layer."""

from __future__ import annotations

import shutil
from pathlib import Path

from src.utils.config import RAW_DIR, RAW_INPUT_PATH


def ensure_raw_dir() -> None:
    """Ensure the raw data directory exists."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def copy_local_raw_file(source_path: Path, destination_dir: Path) -> Path:
    """Copy the local raw file into the Raw layer."""
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / source_path.name
    shutil.copy2(source_path, destination_path)
    return destination_path


def ingest_raw_data() -> Path:
    """
    Ingest raw data into the Raw layer from tickets_raw.json at project root.
    Raises FileNotFoundError if the input file is missing.
    """
    ensure_raw_dir()

    if not RAW_INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {RAW_INPUT_PATH}. "
            "Place tickets_raw.json at the project root or set RAW_INPUT_FILENAME in .env."
        )

    return copy_local_raw_file(RAW_INPUT_PATH, RAW_DIR)
