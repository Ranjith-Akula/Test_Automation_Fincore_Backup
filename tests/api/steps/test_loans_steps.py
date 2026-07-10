import pytest
import os
import json
import requests
from datetime import datetime
from pytest_bdd import scenarios, given, when, then, parsers
from dotenv import load_dotenv
load_dotenv("/workspaces/Test_Automation_Fincore_Backup/app/.env")

scenarios('../features/loans.feature')

@then("All returned loans have status = active")
def check_all_loans_active(api_response):
    data = api_response.json().get("data", [])
    assert len(data) > 0, "Response returned no data to validate"
    for record in data:
        assert record.get("status") == "active", f"Record {record} does not have status 'active'"

    
@then("All fields present including loan_duration_days and emi_amount")
def check_all_fields_present(api_response):
    data = api_response.json().get("data", [])
    assert len(data) > 0, "Response returned no data to validate"
    required_fields = ["loan_duration_days", "emi_amount"]
    for record in data:
        for field in required_fields:
            assert field in record, f"Record {record} missing required field '{field}'"


@then("loan_duration_days matches end_date minus start_date calculation")
def check_loan_duration(api_response):
    data = api_response.json().get("data", [])
    assert len(data) > 0, "Response returned no data to validate"
    for record in data:
        start_date = datetime.fromisoformat(record.get("start_date", "").replace(".000Z", ""))
        end_date = datetime.fromisoformat(record.get("end_date", "").replace(".000Z", ""))
        expected_duration = (end_date - start_date).days
        assert record.get("loan_duration_days") == expected_duration, f"Record {record} has incorrect loan_duration_days"


@then("total_customers match DB counts")
def check_total_loans_match_db_count(api_response, db_connection):
    json_response = api_response.json()
    total_from_api = json_response.get("total_loans")
    assert total_from_api is not None, "Response missing 'total_loans' field"
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM loans")
        total_from_db = cursor.fetchone()[0]
    assert int(total_from_api) == total_from_db, f"API total_loans {total_from_api} does not match DB count {total_from_db}"


@then("active_loans match DB counts")
def check_active_loans_match_db_count(api_response, db_connection):
    json_response = api_response.json()
    active_list = [record for record in json_response.get("data", []) if record.get("status") == "active"]
    total_active_from_api = len(active_list)
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM loans WHERE status = 'active'")
        total_active_from_db = cursor.fetchone()[0]
    assert total_active_from_api == total_active_from_db, f"API active_loans {total_active_from_api} does not match DB count {total_active_from_db}"