"""Configuration and environment variables."""

from __future__ import annotations

import os
from pathlib import Path


def _get_project_root() -> Path:
    """Return the project root directory based on this file location."""
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _get_project_root()


def _load_env_file(env_path: Path) -> None:
    """Load key=value pairs from a .env file using stdlib only."""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_env_file(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
REFERENCE_DIR = DATA_DIR / "reference"

RAW_INPUT_FILENAME = os.getenv("RAW_INPUT_FILENAME", "tickets_raw.json")
RAW_INPUT_PATH = PROJECT_ROOT / RAW_INPUT_FILENAME

HOLIDAY_API_URL = os.getenv("HOLIDAY_API_URL", "https://date.nager.at/api/v3/PublicHolidays")
HOLIDAY_COUNTRY_CODE = os.getenv("HOLIDAY_COUNTRY_CODE", "BR")
DEFAULT_HOLIDAY_YEAR = int(os.getenv("DEFAULT_HOLIDAY_YEAR", "2026"))
