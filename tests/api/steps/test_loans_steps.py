import pytest
import os
import json
import requests
from datetime import datetime
from pytest_bdd import scenarios, given, when, then, parsers
from tests.api.steps.common_steps import *


scenarios('../features/loans.feature')

@then("All returned loans have status = active")
def check_all_loans_active(api_response):
    data = api_response.json().get("data", [])
    assert len(data) > 0, "Response returned no data to validate"
    for record in data:
        assert record.get("status") == "active", f"Record {record} does not have status 'active'"

    
@then("All fields present including loan_duration_days and emi_amount")
def check_all_fields_present(api_response):
    loan = api_response.json()
    assert len(loan) > 0, "Response returned no data to validate"
    assert "loan_duration_days" in loan, "Missing loan_duration_days"
    assert "emi_amount" in loan, "Missing emi_amount"
    assert loan["loan_duration_days"] is not None
    assert loan["emi_amount"] is not None


@then("loan_duration_days matches end_date minus start_date calculation")
def check_loan_duration(api_response):
    loan = api_response.json()
    assert len(loan) > 0, "Response returned no data to validate"
    start_date = datetime.fromisoformat(loan.get("start_date", "").replace(".000Z", ""))
    end_date = datetime.fromisoformat(loan.get("end_date", "").replace(".000Z", ""))
    expected_duration = (end_date - start_date).days
    assert loan.get("loan_duration_days") == expected_duration, f"Record {loan} has incorrect loan_duration_days"


@then("total_customers match DB counts")
def check_total_loans_match_db_count(api_response, db_connection):
    json_response = api_response.json()
    total_from_api = json_response.get("total_customers")
    assert total_from_api is not None, "Response missing 'total_customers' field"
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM customers")
        total_from_db = cursor.fetchone()[0]
    assert int(total_from_api) == total_from_db, f"API total_customers {total_from_api} does not match DB count {total_from_db}"


@then("active_loans match DB counts")
def check_active_loans_match_db_count(api_response, db_connection):
    json_response = api_response.json()
    total_active_from_api = json_response.get("active_loans")
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM loans WHERE status = 'active'")
        total_active_from_db = cursor.fetchone()[0]
    assert total_active_from_api == total_active_from_db, f"API active_loans {total_active_from_api} does not match DB count {total_active_from_db}"