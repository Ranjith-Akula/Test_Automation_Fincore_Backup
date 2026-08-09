import pytest
import os
import requests
from pytest_bdd import scenarios, given, when, then, parsers
import psycopg2
import psycopg2.extras
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from tests.api.steps.common_steps import *

scenarios('../features/transactions.feature')


@then("All returned records have transaction_type = credit")
def check_all_records_credit(api_response):
    data = api_response.json().get("data", [])
    assert len(data) > 0, "Response returned no data to validate"
    for record in data:
        assert record.get("transaction_type") == "credit", f"Record {record} does not have transaction_type 'credit'"


@then("All returned transaction_dates fall within the range")
def check_transaction_dates_within_range(api_response):
    parsed = urlparse(api_response.url)
    params = parse_qs(parsed.query)
    start = datetime.fromisoformat(params["from_date"][0])
    end = datetime.fromisoformat(params["to_date"][0])
    data = api_response.json().get("data", [])
    assert len(data) > 0, "Response returned no data to validate"
    for record in data:
        transaction_date = datetime.fromisoformat(
            record.get("transaction_date", "").replace(".000Z", "")
        )
        assert start <= transaction_date <= end, f"Record {record} has transaction_date outside the range {start} to {end}"


@then("All returned amounts are between 100 and 500")
def check_amounts_between_100_and_500(api_response):
    data = api_response.json().get("data", [])
    assert len(data) > 0, "Response returned no data to validate"
    for record in data:
        amount = record.get("amount")
        assert amount is not None, f"Record {record} missing 'amount'"
        assert 100 <= amount <= 500, f"Record {record} has amount outside the range 100-500"

    
@then("All returned records belong to account_id 5 verified against DB")
def check_records_account_id_5(api_response, db_connection):
    data = api_response.json().get("data", [])
    assert len(data) > 0, "Response returned no data to validate"
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT id FROM transactions WHERE account_id = 5")
        valid_ids = {row[0] for row in cursor.fetchall()}
    for record in data:
        assert record.get("account_id") == 5, f"Record {record} does not have account_id 5"
        assert record.get("id") in valid_ids, f"Record {record} does not match DB record for account_id 5"
