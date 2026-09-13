import pytest
import subprocess
import sys
import csv
import requests
from datetime import datetime

DATA_ROOT = "pipeline"
API_BASE_URL = "http://localhost:4000/api/v1"  
DASHBOARD_URL = "http://localhost:3000/dashboard"  


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
    try:
        with db_connection.cursor() as cur:
            table_row_counts = {}
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                table_row_counts[table] = cur.fetchone()[0]

        csv_row_counts = {}
        for table in tables:
            with open(f"{DATA_ROOT}/{data_dir}/{table}.csv", "r", newline="") as f:
                reader = csv.reader(f)
                next(reader)
                csv_row_counts[table] = sum(1 for _ in reader)

        for table in tables:
            if table_row_counts[table] != csv_row_counts[table]:
                return {
                    "stage": "3_row_count_check", "status": "FAIL",
                    "detail": f"Row count mismatch for table {table}: DB={table_row_counts[table]}, CSV={csv_row_counts[table]}"
                }
        return {"stage": "3_row_count_check", "status": "PASS", "detail": table_row_counts}
    except Exception as e:
        return {"stage": "3_row_count_check", "status": "FAIL", "detail": str(e)}


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

def stage_5_api_counts(db_connection) -> dict:
    """Call the API — assert response counts match DB counts."""
    tables_to_endpoints = {
        "customers": "/api/customers",
        "accounts": "/api/accounts",
        "transactions": "/api/transactions",
        "loans": "/api/loans",
    }
    try:
        with db_connection.cursor() as cur:
            for table, endpoint in tables_to_endpoints.items():
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                db_count = cur.fetchone()[0]

                response = requests.get(f"{API_BASE_URL}{endpoint}")
                response.raise_for_status()
                api_count = len(response.json()) 
                if db_count != api_count:
                    return {
                        "stage": "5_api_counts", "status": "FAIL",
                        "detail": f"{table}: DB={db_count}, API={api_count}"
                    }
        return {"stage": "5_api_counts", "status": "PASS", "detail": "All API counts match DB"}
    except Exception as e:
        return {"stage": "5_api_counts", "status": "FAIL", "detail": str(e)}


# ---------- Stage 6 ----------

def stage_6_computed_field_via_api(db_connection) -> dict:
    """Assert a computed field (loan_duration_days) is correctly returned by the API."""
    try:
        with db_connection.cursor() as cur:
            cur.execute("SELECT loan_id, loan_duration_days FROM loans LIMIT 1")
            row = cur.fetchone()
            if row is None:
                return {"stage": "6_computed_field", "status": "FAIL", "detail": "No loans found in DB to check"}
            loan_id, expected_duration = row

        response = requests.get(f"{API_BASE_URL}/api/loans/{loan_id}")  
        response.raise_for_status()
        api_duration = response.json()["loan_duration_days"]  

        if api_duration != expected_duration:
            return {
                "stage": "6_computed_field", "status": "FAIL",
                "detail": f"loan_duration_days mismatch: DB={expected_duration}, API={api_duration}"
            }
        return {"stage": "6_computed_field", "status": "PASS", "detail": f"loan_duration_days matched: {api_duration}"}
    except Exception as e:
        return {"stage": "6_computed_field", "status": "FAIL", "detail": str(e)}


# ---------- Stage 7 ----------

def stage_7_dashboard_summary_check(db_connection, page) -> dict:
    """Open the browser, navigate to dashboard — assert a summary card value matches DB."""
    try:
        with db_connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM loans")
            expected_count = cur.fetchone()[0]

        page.goto(DASHBOARD_URL)
        summary_locator = page.locator("#total-loans-count")  
        displayed_text = summary_locator.inner_text().strip()
        displayed_count = int(displayed_text)

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

def run_e2e(data_dir: str, db_connection) -> dict:
    results = {}

    results["stage_1_truncate"] = stage_1_truncate_tables(db_connection)
    results["stage_2_run_pipeline"] = stage_2_run_pipeline(data_dir)
    results["stage_3_row_count_check"] = stage_3_row_count_check(db_connection, data_dir)
    results["stage_4_run_gx_validation"] = stage_4_run_gx_validation()

    if results["stage_4_run_gx_validation"]["status"] == "FAIL":
        skip_detail = "Skipped: Stage 4 (GX validation) failed"
        results["stage_5_api_counts"] = {"stage": "5_api_counts", "status": "SKIPPED", "detail": skip_detail}
        results["stage_6_computed_field"] = {"stage": "6_computed_field", "status": "SKIPPED", "detail": skip_detail}
        # results["stage_7_dashboard_check"] = {"stage": "7_dashboard_check", "status": "SKIPPED", "detail": skip_detail}
    else:
        results["stage_5_api_counts"] = stage_5_api_counts(db_connection)
        results["stage_6_computed_field"] = stage_6_computed_field_via_api(db_connection)
        # results["stage_7_dashboard_check"] = stage_7_dashboard_summary_check(db_connection)

    results["stage_8_report"] = stage_8_generate_report(results, data_dir)

    return results


# ---------- pytest entry points ----------

def test_e2e_good_data(db_connection):
    results = run_e2e("good_data", db_connection)
    for stage_name, result in results.items():
        assert result["status"] == "PASS", f"{stage_name} failed: {result['detail']}"


def test_e2e_bad_data(db_connection):
    results = run_e2e("bad_data", db_connection)
    assert results["stage_4_run_gx_validation"]["status"] == "FAIL"
    assert results["stage_5_api_counts"]["status"] == "SKIPPED"
    assert results["stage_6_computed_field"]["status"] == "SKIPPED"
    # assert results["stage_7_dashboard_check"]["status"] == "SKIPPED"