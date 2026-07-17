import os
import pytest
import psycopg2
import requests
from dotenv import load_dotenv
from pathlib import Path
import time
from playwright.sync_api import sync_playwright
from datetime import datetime

load_dotenv("/workspaces/Test_Automation_Fincore_Backup/app/.env")

API_BASE_URL = os.getenv("API_BASE_URL")
BASE_URL = os.getenv("FINCORE_BASE_URL", "http://localhost:3000")

@pytest.fixture(autouse=True)
def rate_limit_delay():
    yield
    time.sleep(0.5)  # 500ms delay after each test


@pytest.fixture(scope="session")
def db_connection():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def auth_token():
    response = requests.post(f"{API_BASE_URL}/auth/login", json={
        "username": os.getenv("TEST_USER_USERNAME"),
        "password": os.getenv("TEST_USER_PASSWORD")
    })
    response.raise_for_status()
    return response.json()["token"]


@pytest.fixture
def api_client(auth_token):
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {auth_token}"})
    return session


# ---------- Playwright fixtures ----------

@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch(headless=True)
    yield browser
    browser.close()

@pytest.fixture
def context(browser):
    context = browser.new_context()
    yield context
    context.close()

@pytest.fixture
def page(context):
    page = context.new_page()
    page.goto(BASE_URL)
    yield page
    page.close()

# ---------- UI test credentials (reuses existing API creds) ----------

@pytest.fixture
def valid_credentials():
    return {
        "username": os.getenv("TEST_USER_USERNAME"),
        "password": os.getenv("TEST_USER_PASSWORD"),
    }

# ---------- Screenshot on failure ----------

@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            screenshot_dir = Path("tests/reports/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            safe_name = item.name.replace("/", "_").replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = screenshot_dir / f"{safe_name}_{timestamp}.png"
            page.screenshot(path=str(path))