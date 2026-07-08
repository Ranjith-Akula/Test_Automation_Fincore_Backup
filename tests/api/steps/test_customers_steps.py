import os
import psycopg2
import psycopg2.extras
import pytest
import requests
from dotenv import load_dotenv
from pytest_bdd import scenarios, given, when, then, parsers

load_dotenv("/workspaces/Test_Automation_Fincore_Backup/app/.env")

API_BASE_URL = os.getenv("API_BASE_URL")

scenarios('../features/customers.feature')


@given("I am authenticated")
def authenticated(api_client):
    pass


@given("I am not authenticated", target_fixture="api_client")
def not_authenticated():
    return requests.Session()


@when(parsers.parse('I GET "{endpoint}"'), target_fixture="api_response")
def get_request(api_client, endpoint):
    return api_client.get(f"{API_BASE_URL}{endpoint}")


@then(parsers.parse('Response is {status_code:d}'))
def check_status_code(api_response, status_code):
    assert api_response.status_code == status_code


@then("data array is non-empty")
def check_data_array(api_response):
    json_response = api_response.json()
    assert "data" in json_response
    assert isinstance(json_response["data"], list)
    assert len(json_response["data"]) > 0


@then("total matches DB count")
def check_total_matches_db_count(api_response, db_connection):
    json_response = api_response.json()
    total_from_api = json_response.get("total")
    assert total_from_api is not None, "Response missing 'total' field"
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM customers")
        total_from_db = cursor.fetchone()[0]
    assert int(total_from_api) == total_from_db


@then("All returned records have status = active")
def check_all_records_active(api_response):
    data = api_response.json().get("data", [])
    assert len(data) > 0, "Response returned no data to validate"
    for record in data:
        assert record.get("status") == "active", f"Record {record} does not have status 'active'"


@pytest.mark.xfail(reason="API search endpoint not filtering correctly - known bug")
@then("All returned names contain JOHN")
def check_all_names_contain_john(api_response):
    data = api_response.json().get("data", [])
    assert len(data) > 0, "Response returned no data to validate"
    for record in data:
        name = record.get("name", "")
        assert "JOHN" in name.upper(), f"Record {record} does not contain 'JOHN' in name"


@then("Response contains customer with id=1 matching DB record")
def check_customer_id_1_matches_db(api_response, db_connection):
    customer_from_api = api_response.json().get("customer")
    assert customer_from_api is not None, "Response missing 'customer' field"
    with db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute("SELECT name, email, status, created_date FROM customers WHERE id = 1")
        customer_from_db = cursor.fetchone()
    assert customer_from_db is not None, "Customer with id=1 not found in database"
    assert customer_from_api.get("name") == customer_from_db["name"]
    assert customer_from_api.get("email") == customer_from_db["email"]
    assert customer_from_api.get("status") == customer_from_db["status"]
    api_date = customer_from_api.get("created_date", "").replace(".000Z", "")
    db_date = customer_from_db["created_date"].strftime("%Y-%m-%dT%H:%M:%S")
    assert api_date == db_date, "Created date does not match"


@then("Response is 404 with error message")
def invalid_customer_id_response(api_response):
    assert api_response.status_code == 404
    json_response = api_response.json()
    assert "error" in json_response
    assert json_response.get("error") is not None