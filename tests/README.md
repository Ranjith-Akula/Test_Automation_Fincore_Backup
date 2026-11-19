# FinCore Bank - Test Automation Guide

[![pytest](https://img.shields.io/badge/pytest-automation-blue.svg)](https://docs.pytest.org/)
[![Playwright](https://img.shields.io/badge/Playwright-UI%20tests-green.svg)](https://playwright.dev/python/)
[![PySpark](https://img.shields.io/badge/PySpark-pipeline-orange.svg)](https://spark.apache.org/docs/latest/api/python/)
[![Great Expectations](https://img.shields.io/badge/Great%20Expectations-data%20quality-purple.svg)](https://greatexpectations.io/)

The `tests/` directory covers the FinCore REST API, browser UI, PySpark
transformations, end-to-end data pipeline, and database data quality.

> **Run commands from the repository root** so Python imports, input data, and
> generated report paths resolve correctly.

## 📚 Contents

- [Test suites](#-test-suites)
- [Prerequisites and setup](#-prerequisites-and-setup)
- [Configuration](#-configuration)
- [Running the tests](#-running-the-tests)
- [Data quality validation](#-data-quality-validation)
- [Reports and screenshots](#-reports-and-screenshots)
- [⚠️ End-to-end database warning](#️-end-to-end-database-warning)

## 🧪 Test suites

| Suite | Location | What it verifies |
| --- | --- | --- |
| **API automation** | [`api/`](api/) | BDD scenarios for authentication, customers, loans, and transactions. Checks status codes, filtering, response fields, computed loan values, and API results against PostgreSQL where applicable. |
| **UI automation** | [`ui/`](ui/) | Playwright scenarios for login/logout, dashboard summary cards, customer search/filter/detail navigation, and transaction filters. Dashboard counts are checked against PostgreSQL. |
| **Pipeline transformations** | [`pipeline/test_transformations.py`](pipeline/test_transformations.py) | PySpark transformation helpers: name/date normalization, defaults, trimming, mappings, loan calculations, filtering, duplicate removal, email validation, and audit columns. Uses small in-memory DataFrames. |
| **Pipeline end-to-end** | [`pipeline/test_e2e.py`](pipeline/test_e2e.py) | Loads good or intentionally bad CSV data, checks database row counts and Great Expectations results, then checks API data and a dashboard count for good data. |
| **Data quality** | [`dq/`](dq/) | Great Expectations rules validate customers, accounts, transactions, and loans in PostgreSQL. Run these validators as scripts; they are not pytest tests. |

API and UI scenarios are described in `api/features/` and `ui/features/`.
Their step implementations live in each suite's `steps/` folder, and UI
Page Object classes are in `ui/pages/`.

## 📋 Prerequisites and setup

### Install Python dependencies

From the repository root:

```powershell
python -m pip install -r pipeline/requirements.txt
```

### Prepare services and browsers

- **API and UI tests:** Start the FinCore backend and frontend. See the root
  [quick start](../README.md#-quick-start) or [local setup guide](../SETUP.md).
- **Database-backed tests:** Start PostgreSQL, initialize the FinCore schema,
  and load test data.
- **Pipeline tests:** Install Java JDK 11 or 17 and use a Python environment
  compatible with PySpark.
- **UI tests:** Install Playwright's Chromium browser once:

  ```powershell
  python -m playwright install chromium
  ```

## ⚙️ Configuration

Pytest fixtures load `app/.env` and `pipeline/.env` from the repository root.
Values can also be supplied through the process environment.

| Setting | Purpose |
| --- | --- |
| `API_BASE_URL` | API root, for example `http://localhost:4000/api/v1`. If unset, `API_PORT` from `app/.env` is used to build the URL. One of these must be set when pytest loads `tests/conftest.py`. |
| `TEST_USER_USERNAME` / `TEST_USER_PASSWORD` | Credentials for API scenarios and the session API token. UI tests use them when provided, otherwise the UI fixture falls back to the local admin test account. |
| `DATABASE_URL` | PostgreSQL connection string used by database-backed pytest fixtures. |
| `FINCORE_BASE_URL` | UI base URL; defaults to `http://localhost:3000`. |
| `fincore_pg_conn` | SQLAlchemy connection string for Great Expectations. Set it in `tests/dq/great_expectations/gx/uncommitted/config_variables.yml` or the environment. |

> **Keep credentials private.** Do not commit real passwords or production
> connection strings to environment or configuration files.

## 🚀 Running the tests

Use these commands from the repository root in PowerShell:

```powershell
# Preview discovered pytest tests
python -m pytest --collect-only -q

# Spark transformation unit tests (no running FinCore services required)
python -m pytest tests/pipeline/test_transformations.py -q

# API scenarios (requires API, PostgreSQL, and test credentials)
python -m pytest tests/api -q

# Browser UI scenarios (requires UI, API, PostgreSQL, and Chromium)
python -m pytest tests/ui -q

# End-to-end run with the clean dataset
python -m pytest tests/pipeline/test_e2e.py -q -k good_data

# End-to-end run with intentionally invalid data
python -m pytest tests/pipeline/test_e2e.py -q -k bad_data

# Entire pytest suite
python -m pytest -q
```

`api` and `ui` marker names are declared in `pytest.ini`; tests are organized
by suite directory, so the directory commands above are the clearest way to
select them.

## ✅ Data quality validation

Run the checkpoint-based validator from the repository root:

```powershell
python tests/dq/run_gx.py
```

The command exits with a non-zero status if any checkpoint expectation fails.
To run validation for each configured table and print expectation-level failure
details directly:

```powershell
python tests/dq/great_expectations/validate.py
```

Expectations are stored in
`tests/dq/great_expectations/gx/expectations/`. The table and suite mapping is
in `tests/dq/great_expectations/rules_config.json`.

## 📊 Reports and screenshots

Generate a self-contained HTML report for a pytest run with `pytest-html`:

```powershell
python -m pytest tests/api -q --html=tests/reports/api_report.html --self-contained-html
```

UI test failures may also save screenshots under
`tests/reports/screenshots/`. End-to-end runs write
`tests/reports/pipeline_report_good.html` or
`tests/reports/pipeline_report_bad.html`.

Great Expectations Data Docs are built under `tests/reports/dq_good/` after a
successful checkpoint validation and `tests/reports/dq_bad/` after a failed
validation.

## ⚠️ End-to-end database warning

`tests/pipeline/test_e2e.py` **truncates the `transactions`, `loans`, `accounts`,
and `customers` tables** before loading data. It replaces the database contents
with either `data/good_data/` or `data/bad_data/`; the bad-data run is expected
to fail Great Expectations validation.

> **Only run end-to-end tests against a disposable local/test database. Never
> point them at a shared or production database.** After a run, the database
> contains whichever dataset was loaded last.
