"""Gold layer: compute SLA metrics for resolved tickets and produce aggregated reports."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Set

import pandas as pd

from src.sla.sla_calculation import (
    calculate_business_hours,
    get_expected_sla_hours,
    get_sla_status,
)
from src.utils.config import (
    DEFAULT_HOLIDAY_YEAR,
    GOLD_DIR,
    HOLIDAY_COUNTRY_CODE,
    SILVER_DIR,
)
from src.utils.date_utils import fetch_public_holidays


def read_silver(silver_path: Path) -> pd.DataFrame:
    """Read Silver data from disk (JSON)."""
    df = pd.read_json(silver_path, orient="records")
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    df["resolved_at"] = pd.to_datetime(df["resolved_at"], errors="coerce", utc=True)
    return df


def filter_resolved(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only Done and Resolved issues."""
    return df[df["status"].isin(["Done", "Resolved"])]


def build_holiday_set(years: Set[int]) -> Set:
    """Fetch holidays for all relevant years."""
    holidays = set()
    for year in years:
        holidays |= fetch_public_holidays(year, country_code=HOLIDAY_COUNTRY_CODE)
    return holidays


def calculate_sla_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate resolution time in business hours, expected SLA, and SLA met indicator."""
    df = df.copy()
    created_years = (
        pd.to_datetime(df["created_at"], errors="coerce", utc=True).dt.year.dropna().unique()
    )
    resolved_years = (
        pd.to_datetime(df["resolved_at"], errors="coerce", utc=True).dt.year.dropna().unique()
    )
    years = set(created_years) | set(resolved_years)
    if not years:
        years = {DEFAULT_HOLIDAY_YEAR}
    holidays = build_holiday_set(years)

    df["resolution_hours"] = df.apply(
        lambda row: calculate_business_hours(
            row["created_at"], row["resolved_at"], holidays
        ),
        axis=1,
    )
    df["sla_expected_hours"] = df["priority"].apply(get_expected_sla_hours)
    df["is_sla_met"] = df.apply(
        lambda row: get_sla_status(
            row["resolution_hours"], row["sla_expected_hours"]
        )
        == "met",
        axis=1,
    )
    return df


def select_gold_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Select final Gold columns for analytics (drop assignee_id, assignee_email if present)."""
    drop_cols = [c for c in ["assignee_id", "assignee_email"] if c in df.columns]
    return df.drop(columns=drop_cols)


def write_gold(df: pd.DataFrame, output_path: Path) -> Path:
    """Write Gold data to disk (JSON)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(output_path, orient="records", date_format="iso", index=False)
    return output_path


def build_sla_reports(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Build aggregated reports: average SLA by analyst and by ticket type."""
    required_cols = {"issue_id", "issue_type", "assignee_name", "resolution_hours"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Gold data is missing required columns: {', '.join(sorted(missing))}")

    by_assignee = (
        df.groupby("assignee_name", dropna=False)
        .agg(
            issue_count=("issue_id", "count"),
            sla_avg_hours=("resolution_hours", "mean"),
        )
        .reset_index()
    )
    by_assignee["sla_avg_hours"] = by_assignee["sla_avg_hours"].round(2)

    by_issue_type = (
        df.groupby("issue_type", dropna=False)
        .agg(
            issue_count=("issue_id", "count"),
            sla_avg_hours=("resolution_hours", "mean"),
        )
        .reset_index()
    )
    by_issue_type["sla_avg_hours"] = by_issue_type["sla_avg_hours"].round(2)

    return {
        "gold_sla_by_analyst.csv": by_assignee,
        "gold_sla_by_issue_type.csv": by_issue_type,
    }


def write_sla_reports(df: pd.DataFrame, output_dir: Path = GOLD_DIR / "reports") -> Dict[str, Path]:
    """Write aggregated SLA reports to disk (CSV)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    reports = build_sla_reports(df)
    output_paths: Dict[str, Path] = {}
    for filename, report_df in reports.items():
        output_path = output_dir / filename
        report_df.to_csv(output_path, index=False)
        output_paths[filename] = output_path
    return output_paths


def run_gold(
    silver_path: Path = SILVER_DIR / "silver_issues.json",
    output_filename: str = "gold_sla_issues.json",
) -> Path:
    """Execute the Gold pipeline."""
    silver_df = read_silver(silver_path)
    resolved = filter_resolved(silver_df)
    with_sla = calculate_sla_metrics(resolved)
    final_df = select_gold_columns(with_sla)
    output_path = GOLD_DIR / output_filename
    write_gold(final_df, output_path)
    write_sla_reports(final_df)
    return output_path
