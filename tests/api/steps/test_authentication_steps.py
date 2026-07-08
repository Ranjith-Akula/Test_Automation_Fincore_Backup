import pytest
import requests
import os
from dotenv import load_dotenv
from pytest_bdd import scenarios, given, when, then, parsers


load_dotenv("/workspaces/Test_Automation_Fincore_Backup/app/.env")

API_BASE_URL = os.getenv("API_BASE_URL")

scenarios('../features/authentication.feature')


@given("A registered user exists", target_fixture="api_client")
def registered_user_exists():
    # Create a session for the registered user
    session = requests.Session()
    # Here you would typically perform a registration step or ensure the user exists in the system.
    return session


@given("No credentials provided", target_fixture="api_client")
def missing_credentials():
    # Create a session for the user with missing credentials
    session = requests.Session()
    return session


@when(parsers.parse('I POST valid credentials to "{endpoint}"'), target_fixture="api_response")
def post_valid_credentials(api_client, endpoint):
    payload = {
        "username": os.getenv("TEST_USER_USERNAME"),
        "password": os.getenv("TEST_USER_PASSWORD")
    }
    return api_client.post(f"{API_BASE_URL}{endpoint}", json=payload)


@when(parsers.parse('I POST wrong password to "{endpoint}"'), target_fixture="api_response")
def post_wrong_password(api_client, endpoint):
    payload = {
        "username": os.getenv("TEST_USER_USERNAME"),
        "password": "wrong_password"
    }
    return api_client.post(f"{API_BASE_URL}{endpoint}", json=payload)


@when(parsers.parse('I POST empty body to "{endpoint}"'), target_fixture="api_response")
def post_missing_credentials(api_client, endpoint):
    payload = {}
    return api_client.post(f"{API_BASE_URL}{endpoint}", json=payload)


@then("Response is 200")
def check_response_200(api_response):
    assert api_response.status_code == 200


@then("response contains a JWT token")
def check_jwt_token(api_response):
    assert "token" in api_response.json()


@then("Response is 401 with an error message")
def check_response_401(api_response):
    assert api_response.status_code == 401
    json_response = api_response.json()
    assert "error" in json_response
    assert json_response["error"] is not None


@then("Response is 400 with validation error")
def check_response_400(api_response):
    assert api_response.status_code == 400
    json_response = api_response.json()
    assert "error" in json_response
    assert json_response["error"] is not None