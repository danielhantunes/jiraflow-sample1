"""Silver layer: extract fields, clean data, apply quality checks and filter statuses."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils.config import SILVER_DIR


def read_bronze(bronze_path: Path) -> pd.DataFrame:
    """Read Bronze data from disk (JSON)."""
    return pd.read_json(bronze_path, orient="records")


def _normalize_items(items: object) -> list | None:
    if isinstance(items, list):
        return items
    if hasattr(items, "tolist"):
        try:
            return items.tolist()
        except Exception:
            return None
    return None


def _first_item_value(series: pd.Series, key: str) -> pd.Series:
    def _extract(items: object) -> object:
        normalized = _normalize_items(items)
        if normalized and isinstance(normalized[0], dict):
            return normalized[0].get(key, pd.NA)
        return pd.NA
    return series.apply(_extract)


def extract_and_rename_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Extract nested fields (assignee, timestamps) and standardize column names."""
    selected = df.copy()

    if "assignee" in selected.columns:
        selected["assignee_name"] = _first_item_value(selected["assignee"], "name")
        selected["assignee_id"] = _first_item_value(selected["assignee"], "id")
        selected["assignee_email"] = _first_item_value(selected["assignee"], "email")

    if "timestamps" in selected.columns:
        selected["created_at"] = _first_item_value(selected["timestamps"], "created_at")
        selected["resolved_at"] = _first_item_value(selected["timestamps"], "resolved_at")

    columns_map = {
        "id": "issue_id",
        "issue_type": "issue_type",
        "status": "status",
        "priority": "priority",
        "assignee_name": "assignee_name",
        "assignee_id": "assignee_id",
        "assignee_email": "assignee_email",
        "created_at": "created_at",
        "resolved_at": "resolved_at",
    }

    if "id" in selected.columns:
        selected["issue_id"] = selected["id"].astype("string")

    legacy_map = {
        "fields.issuetype.name": "issue_type",
        "fields.assignee.displayName": "assignee_name",
        "fields.priority.name": "priority",
        "fields.status.name": "status",
        "fields.created": "created_at",
        "fields.resolutiondate": "resolved_at",
    }
    for source_col, target_col in legacy_map.items():
        if target_col not in selected.columns and source_col in selected.columns:
            selected[target_col] = selected[source_col]

    for target_col in columns_map.values():
        if target_col not in selected.columns:
            selected[target_col] = pd.NA

    return selected[list(columns_map.values())]


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize data types and formats."""
    df = df.copy()
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    df["resolved_at"] = pd.to_datetime(df["resolved_at"], errors="coerce", utc=True)
    df["status"] = df["status"].astype("string").str.strip().str.title()
    df["priority"] = df["priority"].astype("string").str.strip().str.title()
    if "assignee_name" in df.columns:
        df["assignee_name"] = df["assignee_name"].fillna("Unassigned")
    df["created_at"] = df["created_at"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df["resolved_at"] = df["resolved_at"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return df


def filter_valid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows with valid issue_id and created_at; drop duplicates by issue_id."""
    df = df.copy()
    valid = df[df["issue_id"].notna() & df["created_at"].notna()]
    return valid[~valid["issue_id"].duplicated(keep="first")]


def filter_statuses(df: pd.DataFrame) -> pd.DataFrame:
    """Keep Open, Done, and Resolved statuses (Open excluded from SLA in Gold)."""
    return df[df["status"].isin(["Open", "Done", "Resolved"])]


def write_silver(df: pd.DataFrame, output_path: Path) -> Path:
    """Write Silver data to disk (JSON)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(output_path, orient="records", date_format="iso", index=False)
    return output_path


def run_silver(bronze_path: Path, output_filename: str = "silver_issues.json") -> Path:
    """Execute the Silver pipeline; output is clean data only in data/silver/."""
    bronze_df = read_bronze(bronze_path)
    extracted = extract_and_rename_fields(bronze_df)
    cleaned = clean_data(extracted)
    valid = filter_valid_rows(cleaned)
    filtered = filter_statuses(valid)
    output_path = SILVER_DIR / output_filename
    return write_silver(filtered, output_path)
