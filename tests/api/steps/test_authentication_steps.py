import pytest
import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from pytest_bdd import scenarios, given, when, then, parsers
from tests.api.steps.common_steps import *

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / "app" / ".env")
load_dotenv(REPO_ROOT / "pipeline" / ".env")

API_BASE_URL = os.getenv("API_BASE_URL")
if not API_BASE_URL:
    api_port = os.getenv("API_PORT")
    if api_port:
        API_BASE_URL = f"http://localhost:{api_port}/api/v1"

TEST_USER_USERNAME = os.getenv("TEST_USER_USERNAME")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD")

if not API_BASE_URL:
    raise RuntimeError(
        "Missing API_BASE_URL. Set API_BASE_URL in pipeline/.env or API_PORT in app/.env."
    )

if not TEST_USER_USERNAME or not TEST_USER_PASSWORD:
    raise RuntimeError(
        "Missing TEST_USER_USERNAME/TEST_USER_PASSWORD. Set them in app/.env or pipeline/.env."
    )
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
        "username": TEST_USER_USERNAME,
        "password": TEST_USER_PASSWORD
    }
    return api_client.post(f"{API_BASE_URL}{endpoint}", json=payload)


@when(parsers.parse('I POST wrong password to "{endpoint}"'), target_fixture="api_response")
def post_wrong_password(api_client, endpoint):
    payload = {
        "username": TEST_USER_USERNAME,
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