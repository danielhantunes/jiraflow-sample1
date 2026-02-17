# jiraflow-sample1 — Medallion Data Pipeline

## Overview

This repository implements a **data engineering pipeline** that ingests ticket/issue data from a local **tickets_raw.json** file, processes it through a **Medallion architecture (Bronze → Silver → Gold)**, and produces SLA metrics plus aggregated reports.

---

## Quick start

Put **tickets_raw.json** at the project root (or set `INPUT_FILENAME` in `.env`).

```bash
pip install -r requirements.txt
python -m src.main
```

---

## Architecture — Medallion Layers

| Layer   | Responsibility |
|--------|-----------------|
| **Bronze** | Normalize and flatten source JSON (JSON) |
| **Silver** | Extract nested fields, clean, validate, filter statuses (JSON; clean data only) |
| **Gold**   | Resolved/Done issues only; SLA in business hours and reports |

```
Bronze  →  Silver  →  Gold
   |         |         |
data/bronze  data/silver  data/gold
                          (reports)
```

---

## How to Run

### Optional: virtual environment

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Provide input data

Place the ticket export at the project root as **tickets_raw.json** (or set `INPUT_FILENAME` in `.env` to another filename at the project root). The JSON must have an **`issues`** array; each issue can have `id`, `issue_type`, `status`, `priority`, and nested **`assignee`** / **`timestamps`** arrays (see `tickets_raw.json` in the repo for the expected shape).

### Run the full pipeline

```bash
python -m src.main
```

Outputs are written under `data/`: bronze JSON, silver JSON (clean data only), gold JSON and **CSV reports** under `data/gold/reports/`.

---

## Output files

- `data/bronze/bronze_issues.json`
- `data/silver/silver_issues.json`
- `data/gold/gold_sla_issues.json`
- `data/gold/reports/gold_sla_by_analyst.csv`
- `data/gold/reports/gold_sla_by_issue_type.csv`

---

## Gold layer — final table and reports

### Final table (SLA per ticket)

Only tickets with status **Done** or **Resolved** are included. Columns include:

- Ticket ID (`issue_id`)
- Ticket type (`issue_type`)
- Responsible analyst (`assignee_name`)
- Priority
- Open date (`created_at`)
- Resolution date (`resolved_at`)
- Resolution time in business hours (`resolution_hours`)
- Expected SLA in hours (`sla_expected_hours`)
- SLA met indicator (`is_sla_met`)

### Reports (CSV)

- **Average SLA by analyst:** Analyst, number of tickets, average SLA (hours).
- **Average SLA by ticket type:** Ticket type, number of tickets, average SLA (hours).

---

## SLA logic

- Resolution time is computed in **business hours** (weekdays, excluding national holidays).
- Each business day counts as 24 hours.
- Expected SLA by priority: High 24 h, Medium 72 h, Low 120 h.
- SLA is **met** when `resolution_hours ≤ sla_expected_hours`.

---

## Environment variables

Copy `.env.example` to `.env` and adjust if needed.

- **INPUT_FILENAME** — default `tickets_raw.json` (file at project root).
- **HOLIDAY_API_URL**, **HOLIDAY_COUNTRY_CODE** — used to fetch public holidays (cached under `data/reference/`).
- **DEFAULT_HOLIDAY_YEAR** — used only when the data has no valid `created_at`/`resolved_at` years; otherwise years are taken from the data.

---

## Project structure

```
project_root/
├── data/
│   ├── bronze/
│   ├── silver/
│   ├── reference/
│   └── gold/
│       └── reports/
├── src/
│   ├── ingestion/   # Bronze ingestion (source file path)
│   ├── bronze/      # Normalization
│   ├── silver/      # Cleaning, validation, filtering
│   ├── gold/        # SLA and reports
│   ├── sla/         # SLA calculation utilities
│   └── utils/       # Config and date helpers
├── .env.example
├── README.md
├── requirements.txt
└── tickets_raw.json (sample)
```

---

## Design notes

- **Local file only:** Input is **tickets_raw.json** at the project root (or the file set by **INPUT_FILENAME**); no cloud or Azure integration.
- **JSON** for Bronze/Silver/Gold (array of records; CSV for gold reports).
- **Silver** outputs only clean data (invalid/duplicate rows are dropped, not persisted).
- **Holiday data** is cached under `data/reference/` to avoid repeated API calls.
