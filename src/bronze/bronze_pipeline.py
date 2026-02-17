"""Bronze layer: normalize and flatten raw ticket JSON to a tabular structure."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence, Union

import pandas as pd

from src.utils.config import BRONZE_DIR


def read_raw_json(raw_file_path: Path) -> Dict:
    """Read the raw JSON file from disk."""
    with raw_file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_raw_schema(raw_json: Dict) -> None:
    """Validate minimal raw JSON structure (must have 'issues' list)."""
    if "issues" not in raw_json:
        raise ValueError("Raw JSON is missing required 'issues' field.")
    if not isinstance(raw_json["issues"], list):
        raise ValueError("Raw JSON 'issues' field must be a list.")


def normalize_issues(raw_json: Dict) -> pd.DataFrame:
    """Normalize nested ticket JSON into a flat table."""
    validate_raw_schema(raw_json)
    issues = raw_json.get("issues", [])
    return pd.json_normalize(issues)


def add_source_file(df: pd.DataFrame, source_file: Path) -> pd.DataFrame:
    """Add source file column for lineage."""
    df = df.copy()
    df["source_file"] = source_file.name
    return df


def write_bronze(df: pd.DataFrame, output_path: Path) -> Path:
    """Write Bronze data to disk (JSON)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(output_path, orient="records", date_format="iso", index=False)
    return output_path


RawPathInput = Union[Path, str, Sequence[Path], Sequence[str]]


def _coerce_raw_paths(raw_file_path: RawPathInput) -> List[Path]:
    if isinstance(raw_file_path, (Path, str)):
        return [Path(raw_file_path)]
    return [Path(p) for p in raw_file_path]


def run_bronze(
    raw_file_path: RawPathInput,
    output_filename: str = "bronze_issues.json",
) -> Path:
    """Execute the Bronze pipeline."""
    raw_paths = _coerce_raw_paths(raw_file_path)
    frames: List[pd.DataFrame] = []
    for path in raw_paths:
        raw_json = read_raw_json(path)
        normalized = normalize_issues(raw_json)
        normalized = add_source_file(normalized, path)
        frames.append(normalized)
    bronze_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    output_path = BRONZE_DIR / output_filename
    return write_bronze(bronze_df, output_path)
