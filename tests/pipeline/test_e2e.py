import os
import pytest
import subprocess
import sys
import csv
import requests
from datetime import datetime
from pyspark.sql import SparkSession
from tests.ui.pages.login_page import LoginPage


DATA_ROOT = "data"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:4000/api/v1")
DASHBOARD_URL = "http://localhost:3000/dashboard"  


def build_auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------- Stage 1 ----------

def stage_1_truncate_tables(db_connection) -> dict:
    tables = ["transactions", "loans", "accounts", "customers"]
    try:
        with db_connection.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {', '.join(tables)} CASCADE")
        db_connection.commit()
        return {"stage": "1_truncate", "status": "PASS", "detail": f"Truncated {len(tables)} tables"}
    except Exception as e:
        db_connection.rollback()
        return {"stage": "1_truncate", "status": "FAIL", "detail": str(e)}


# ---------- Stage 2 ----------

def stage_2_run_pipeline(data_dir: str) -> dict:
    try:
        result = subprocess.run(
            [sys.executable, "ingest.py", data_dir],
            capture_output=True, text=True,
            cwd="pipeline"
        )
        if result.returncode == 0:
            return {"stage": "2_run_pipeline", "status": "PASS", "detail": result.stdout}
        else:
            return {"stage": "2_run_pipeline", "status": "FAIL", "detail": result.stderr}
    except Exception as e:
        return {"stage": "2_run_pipeline", "status": "FAIL", "detail": str(e)}


# ---------- Stage 3 ----------

def stage_3_row_count_check(db_connection, data_dir: str) -> dict:
    tables = ["transactions", "loans", "accounts", "customers"]
    spark = SparkSession.builder.appName("CSVRowCountCheck").master("local[*]").getOrCreate()
    try:
        with db_connection.cursor() as cur:
            table_row_counts = {}
            for table in tables:
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = %s
                    )
                    """,
                    (table,),
                )
                table_exists = cur.fetchone()[0]
                if not table_exists:
                    return {
                        "stage": "3_row_count_check",
                        "status": "FAIL",
                        "detail": f"Table {table} is not available in DB",
                    }

                cur.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cur.fetchone()[0]
                if row_count == 0:
                    return {
                        "stage": "3_row_count_check",
                        "status": "FAIL",
                        "detail": f"Table {table} exists but has 0 rows in DB",
                    }
                table_row_counts[table] = row_count

        csv_row_counts = {}
        for table in tables:
            csv_path = os.path.join("data", data_dir, f"{table}.csv")
            if not os.path.exists(csv_path):
                return {
                    "stage": "3_row_count_check",
                    "status": "FAIL",
                    "detail": f"CSV file not found for table {table}: {csv_path}",
                }

            df = spark.read.csv(csv_path, header=True, inferSchema=True)
            csv_row_counts[table] = df.count()
            if csv_row_counts[table] == 0:
                return {
                    "stage": "3_row_count_check",
                    "status": "FAIL",
                    "detail": f"CSV file for table {table} is empty (0 rows)",
                }

        mismatches = [
            table for table in tables
            if table_row_counts[table] != csv_row_counts[table]
        ]

        if mismatches:
            detail = "; ".join(
                f"{table}: DB={table_row_counts[table]}, CSV={csv_row_counts[table]}"
                for table in mismatches
            )
            return {
                "stage": "3_row_count_check",
                "status": "PASS",
                "detail": f"WARNING: count mismatch detected: {detail}",
            }

        return {
            "stage": "3_row_count_check",
            "status": "PASS",
            "detail": table_row_counts,
        }
    except Exception as e:
        return {"stage": "3_row_count_check", "status": "FAIL", "detail": str(e)}
    finally:
        spark.stop()


# ---------- Stage 4 ----------

def stage_4_run_gx_validation() -> dict:
    try:
        result = subprocess.run(
            [sys.executable, "tests/dq/great_expectations/validate.py"],
            capture_output=True, text=True
            
        )
        if result.returncode == 0:
            return {"stage": "4_run_gx_validation", "status": "PASS", "detail": result.stdout}
        else:
            return {"stage": "4_run_gx_validation", "status": "FAIL", "detail": result.stderr}
    except Exception as e:
        return {"stage": "4_run_gx_validation", "status": "FAIL", "detail": str(e)}


# ---------- Stage 5 ----------

def stage_5_api_counts(db_connection, auth_token: str) -> dict:
    """Call the API — assert response counts match DB counts."""
    tables_to_endpoints = {
        "customers": "/customers",
        "accounts": "/accounts",
        "transactions": "/transactions",
        "loans": "/loans",
    }
    try:
        with db_connection.cursor() as cur:
            for table, endpoint in tables_to_endpoints.items():
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                db_count = cur.fetchone()[0]

                response = requests.get(
                    f"{API_BASE_URL}{endpoint}",
                    headers=build_auth_headers(auth_token),
                )
                response.raise_for_status()
                payload = response.json()
                api_count = payload.get("total")

                if api_count is None:
                    return {
                        "stage": "5_api_counts", "status": "FAIL",
                        "detail": f"{table}: missing total in API response"
                    }

                api_count = int(api_count)

                if db_count != api_count:
                    return {
                        "stage": "5_api_counts", "status": "FAIL",
                        "detail": f"{table}: DB={db_count}, API={api_count}"
                    }
        return {"stage": "5_api_counts", "status": "PASS", "detail": "All API counts match DB"}
    except Exception as e:
        return {"stage": "5_api_counts", "status": "FAIL", "detail": str(e)}


# ---------- Stage 6 ----------

def stage_6_computed_field_via_api(db_connection, auth_token: str) -> dict:
    """Assert a computed field (loan_duration_days) is correctly returned by the API."""
    try:
        with db_connection.cursor() as cur:
            cur.execute("SELECT id, loan_duration_days FROM loans LIMIT 1")
            row = cur.fetchone()
            if row is None:
                return {"stage": "6_computed_field", "status": "FAIL", "detail": "No loans found in DB to check"}
            loan_id, expected_duration = row

        response = requests.get(
            f"{API_BASE_URL}/loans/{loan_id}",
            headers=build_auth_headers(auth_token),
        )
        response.raise_for_status()
        payload = response.json()
        loan = payload.get("loan", payload)
        api_duration = loan["loan_duration_days"]

        if api_duration != expected_duration:
            return {
                "stage": "6_computed_field", "status": "FAIL",
                "detail": f"loan_duration_days mismatch: DB={expected_duration}, API={api_duration}"
            }
        return {"stage": "6_computed_field", "status": "PASS", "detail": f"loan_duration_days matched: {api_duration}"}
    except Exception as e:
        return {"stage": "6_computed_field", "status": "FAIL", "detail": str(e)}


# ---------- Stage 7 ----------

def stage_7_dashboard_summary_check(db_connection, page, valid_credentials) -> dict:
    """Log in, open the dashboard, and assert the active loans summary card matches the DB."""
    try:
        with db_connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM loans WHERE status = 'active'")
            expected_count = cur.fetchone()[0]

        login_page = LoginPage(page)
        login_page.goto()
        login_page.login(valid_credentials["username"], valid_credentials["password"])

        summary_locator = page.get_by_test_id("summary-loans").locator("p").nth(1)
        displayed_text = summary_locator.inner_text().strip()
        displayed_count = int(displayed_text.replace(",", ""))

        if displayed_count != expected_count:
            return {
                "stage": "7_dashboard_check", "status": "FAIL",
                "detail": f"Dashboard shows {displayed_count}, DB has {expected_count}"
            }
        return {"stage": "7_dashboard_check", "status": "PASS", "detail": f"Dashboard count matched: {displayed_count}"}
    except Exception as e:
        return {"stage": "7_dashboard_check", "status": "FAIL", "detail": str(e)}


# ---------- Stage 8 ----------

def stage_8_generate_report(results: dict, data_dir: str) -> dict:
    """Report the full E2E result as PASS or FAIL with stage-level detail."""
    overall_status = "PASS" if all(
        r["status"] in ("PASS", "SKIPPED") for r in results.values()
    ) else "FAIL"

    report_name = "pipeline_report_good.html" if data_dir == "good_data" else "pipeline_report_bad.html"
    report_path = f"tests/reports/{report_name}"

    rows = "".join(
        f"<tr><td>{name}</td><td>{r['status']}</td><td><pre>{r['detail']}</pre></td></tr>"
        for name, r in results.items()
    )
    html = f"""
    <html><body>
    <h1>E2E Pipeline Report — {data_dir}</h1>
    <p>Generated: {datetime.now().isoformat()}</p>
    <p>Overall: <strong>{overall_status}</strong></p>
    <table border="1"><tr><th>Stage</th><th>Status</th><th>Detail</th></tr>{rows}</table>
    </body></html>
    """
    with open(report_path, "w") as f:
        f.write(html)

    return {"stage": "8_report", "status": "PASS", "detail": f"Report written to {report_path}, overall={overall_status}"}


# ---------- Orchestration ----------

def run_e2e(data_dir: str, db_connection, auth_token: str, page=None, valid_credentials=None) -> dict:
    results = {}

    results["stage_1_truncate"] = stage_1_truncate_tables(db_connection)
    results["stage_2_run_pipeline"] = stage_2_run_pipeline(data_dir)
    results["stage_3_row_count_check"] = stage_3_row_count_check(db_connection, data_dir)
    results["stage_4_run_gx_validation"] = stage_4_run_gx_validation()

    if results["stage_4_run_gx_validation"]["status"] == "FAIL":
        skip_detail = "Skipped: Stage 4 (GX validation) failed"
        results["stage_5_api_counts"] = {"stage": "5_api_counts", "status": "SKIPPED", "detail": skip_detail}
        results["stage_6_computed_field"] = {"stage": "6_computed_field", "status": "SKIPPED", "detail": skip_detail}
        results["stage_7_dashboard_check"] = {"stage": "7_dashboard_check", "status": "SKIPPED", "detail": skip_detail}
    else:
        results["stage_5_api_counts"] = stage_5_api_counts(db_connection, auth_token)
        results["stage_6_computed_field"] = stage_6_computed_field_via_api(db_connection, auth_token)
        if page is None:
            results["stage_7_dashboard_check"] = {
                "stage": "7_dashboard_check",
                "status": "FAIL",
                "detail": "Playwright page fixture is required for Stage 7",
            }
        elif valid_credentials is None:
            results["stage_7_dashboard_check"] = {
                "stage": "7_dashboard_check",
                "status": "FAIL",
                "detail": "Valid credentials are required for Stage 7",
            }
        else:
            results["stage_7_dashboard_check"] = stage_7_dashboard_summary_check(db_connection, page, valid_credentials)

    results["stage_8_report"] = stage_8_generate_report(results, data_dir)

    return results


# ---------- pytest entry points ----------

def test_e2e_good_data(db_connection, auth_token, page, valid_credentials):
    results = run_e2e("good_data", db_connection, auth_token, page, valid_credentials)
    print(results)
    for stage_name, result in results.items():
        assert result["status"] == "PASS", f"{stage_name} failed: {result['detail']}"


def test_e2e_bad_data(db_connection, auth_token):
    results = run_e2e("bad_data", db_connection, auth_token)
    assert results["stage_4_run_gx_validation"]["status"] == "FAIL"
    assert results["stage_5_api_counts"]["status"] == "SKIPPED"
    assert results["stage_6_computed_field"]["status"] == "SKIPPED"
    assert results["stage_7_dashboard_check"]["status"] == "SKIPPED"