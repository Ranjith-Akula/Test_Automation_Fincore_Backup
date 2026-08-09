import os
from urllib.parse import urlparse
from pathlib import Path
import requests
from pytest_bdd import given, when, then, parsers
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / "app" / ".env")
load_dotenv(REPO_ROOT / "pipeline" / ".env")

API_BASE_URL = os.getenv("API_BASE_URL")
if not API_BASE_URL:
    api_port = os.getenv("API_PORT")
    if api_port:
        API_BASE_URL = f"http://localhost:{api_port}/api/v1"

if not API_BASE_URL:
    raise RuntimeError(
        "Missing API_BASE_URL. Set API_BASE_URL in pipeline/.env or API_PORT in app/.env."
    )


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


@then("total matches DB count")
def check_total_matches_db_count(api_response, db_connection):
    path = urlparse(api_response.url).path
    table_name = path.strip("/").split("/")[-1]  #Get table name from path
    json_response = api_response.json()
    total_from_api = json_response.get("total")
    assert total_from_api is not None, "Response missing 'total' field"
    with db_connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_from_db = cursor.fetchone()[0]
    assert int(total_from_api) == total_from_db