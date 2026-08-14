import os
import pytest
import psycopg2
import requests
from dotenv import load_dotenv
from pathlib import Path
import time
from playwright.sync_api import sync_playwright
from datetime import datetime
import pytest_html

REPO_ROOT = Path(__file__).resolve().parents[1]
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
    """Starts the actual Playwright engine/driver process"""
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def browser(playwright_instance):
    """Launches a browser instance for the entire test session"""
    browser = playwright_instance.chromium.launch(headless=True)
    yield browser
    browser.close()

@pytest.fixture
def context(browser):
    """Creates a new browser context for each test, ensuring isolation"""
    context = browser.new_context(base_url=BASE_URL)
    yield context
    context.close()

@pytest.fixture
def page(context):
    """Creates a new page in the browser context and navigates to the base URL"""
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
    """Hook to take a screenshot on test failure for UI tests."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = None
        request_obj = item.funcargs.get("request")
        if request_obj:
            try:
                page = request_obj.getfixturevalue("page")
            except pytest.FixtureLookupError:
                pass
            if page is None:
                try:
                    login_page = request_obj.getfixturevalue("login_page")
                    page = getattr(login_page, "page", None)
                except pytest.FixtureLookupError:
                    pass
        if page:
            try:
                screenshot_dir = Path("tests/reports/screenshots")
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                safe_name = item.name.replace("/", "_").replace(" ", "_")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = screenshot_dir / f"{safe_name}_{timestamp}.png"
                page.screenshot(path=str(path))
                # Embed screenshot in the pytest-html report
                try:
                    from pytest_html import extras as html_extras
                    png_b64 = page.screenshot()
                    import base64
                    b64 = base64.b64encode(png_b64).decode("utf-8")
                    if not hasattr(report, "extras"):
                        report.extras = []
                    report.extras.append(html_extras.image(b64, mime_type="image/png"))
                except Exception:
                    pass
            except Exception:
                pass
            
