import os
import pytest
import psycopg2
import requests
from dotenv import load_dotenv
from pathlib import Path
import time

load_dotenv("/workspaces/Test_Automation_Fincore_Backup/app/.env")

API_BASE_URL = os.getenv("API_BASE_URL")

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