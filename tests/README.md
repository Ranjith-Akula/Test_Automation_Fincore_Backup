# FinCore test guide

This directory contains API, browser UI, data pipeline, and data quality tests for
FinCore. Most pytest commands should be run from the repository root so imports,
data paths, and generated report paths resolve correctly.

## Test suites

| Suite | Location | What it covers |
| --- | --- | --- |
| API | `tests/api/` | Pytest-BDD scenarios for authentication, customers, loans, and transactions. Checks status codes, filtering, response fields, computed loan values, and (where applicable) API results against PostgreSQL. |
| UI | `tests/ui/` | Playwright scenarios for login/logout, dashboard summary counts, customer search/filter/detail navigation, and transaction filters. The dashboard checks compare displayed values with PostgreSQL. |
| Pipeline transformations | `tests/pipeline/test_transformations.py` | Unit tests for PySpark transformation helpers, including name/date normalization, defaults, trimming, mappings, loan calculations, filtering, duplicate removal, email validation, and audit columns. Uses small in-memory DataFrames. |
| Pipeline end-to-end | `tests/pipeline/test_e2e.py` | Runs ingestion using good or bad CSV data, checks database row counts and Great Expectations results, then (for good data) checks API counts, a computed loan field, and a dashboard count. Writes an HTML pipeline report. |
| Data quality | `tests/dq/` | Great Expectations validation of customers, accounts, transactions, and loans against the configured PostgreSQL datasource. This is run as a script, not as a pytest suite. |

BDD feature files under `api/features/` and `ui/features/` describe the scenarios;
the corresponding `steps/` files implement them. Page objects for browser tests
are in `ui/pages/`.

## Prerequisites and configuration

Install the Python dependencies from the repository root:

```powershell
python -m pip install -r pipeline/requirements.txt
```

The Spark-based tests also need Java (JDK 11 or 17) and a compatible Python
environment. For browser tests, install Playwright's Chromium browser once:

```powershell
python -m playwright install chromium
```

The API and UI suites require the relevant FinCore services to be running. Tests
that query database state need PostgreSQL loaded with the expected tables and
data. The end-to-end suite additionally runs the data ingestion pipeline itself.
See the repository's [setup guide](../SETUP.md) for starting and configuring the
application and database.

The test fixtures load `app/.env` and `pipeline/.env` from the repository root.
Configure the following values in one of those files or in the process
environment, as appropriate:

| Setting | Used for |
| --- | --- |
| `API_BASE_URL` | API root, for example `http://localhost:4000/api/v1`. If unset, `API_PORT` from `app/.env` is used to form this URL. A base URL or API port is required when pytest loads `tests/conftest.py`. |
| `TEST_USER_USERNAME`, `TEST_USER_PASSWORD` | Credentials required when collecting/running API scenarios and for the session API token. The UI fixture also uses these when provided; it otherwise falls back to the local admin test account. |
| `DATABASE_URL` | PostgreSQL connection used by database-backed pytest fixtures. |
| `FINCORE_BASE_URL` | UI base URL; defaults to `http://localhost:3000`. |
| `fincore_pg_conn` | Great Expectations SQLAlchemy connection string, read by `tests/dq/great_expectations/gx/great_expectations.yml` from its uncommitted config variables or the environment. |

Do not commit real credentials or production connection strings to these files.

## Running pytest

Run commands from the repository root:

```powershell
# Collect tests without executing them
python -m pytest --collect-only -q

# Spark transformation unit tests
python -m pytest tests/pipeline/test_transformations.py -q

# API scenarios
python -m pytest tests/api -q

# Browser UI scenarios
python -m pytest tests/ui -q

# End-to-end test for the clean dataset
python -m pytest tests/pipeline/test_e2e.py -q -k good_data

# End-to-end test for the intentionally invalid dataset
python -m pytest tests/pipeline/test_e2e.py -q -k bad_data

# All pytest tests
python -m pytest -q
```

The `api` and `ui` marker names are declared in `pytest.ini`; selecting by
directory (as above) is the reliable way to run those suites.

To create a self-contained HTML report, for example for API tests:

```powershell
python -m pytest tests/api -q --html=tests/reports/api_report.html --self-contained-html
```

UI failures may also save screenshots under `tests/reports/screenshots/`.

## Running data quality validation

From the repository root, run the checkpoint-based validator:

```powershell
python tests/dq/run_gx.py
```

It exits with a non-zero status if validation fails. It builds Great Expectations
Data Docs in `tests/reports/dq_good/` after a successful validation or
`tests/reports/dq_bad/` after a failed validation.

To validate each configured table and print expectation-level failure details
without running the checkpoint:

```powershell
python tests/dq/great_expectations/validate.py
```

Expectations are defined in the suites under
`tests/dq/great_expectations/gx/expectations/`; the table and datasource mapping
is in `tests/dq/great_expectations/rules_config.json`.

## Important: end-to-end tests change database contents

`tests/pipeline/test_e2e.py` truncates the `transactions`, `loans`, `accounts`,
and `customers` tables before loading a dataset. It replaces the database
contents with either `data/good_data/` or `data/bad_data/`; the bad-data case is
expected to fail Great Expectations validation. Run these tests only against a
disposable local/test database, never a shared or production database. After
running them, the database contains whichever dataset was loaded last.

The generated end-to-end reports are
`tests/reports/pipeline_report_good.html` and
`tests/reports/pipeline_report_bad.html`.
