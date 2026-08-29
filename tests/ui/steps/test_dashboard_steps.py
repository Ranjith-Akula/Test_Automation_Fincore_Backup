import pytest
from tests.ui.pages.dashboard_page import DashboardPage
from pytest_bdd import given, when, then, scenarios
import re
from playwright.sync_api import expect
from tests.ui.pages.login_page import LoginPage

scenarios("../features/dashboard.feature")


#Login to dashboard
@pytest.fixture
def dashboard_page(page, valid_credentials):
    lp = LoginPage(page)
    lp.goto()
    lp.login(valid_credentials["username"], valid_credentials["password"])
    expect(lp.page).to_have_url(re.compile(r".*/dashboard$"))
    return DashboardPage(page)

# --- Total Customers Count ---

@given("I am on the dashboard")
def on_dashboard(dashboard_page):
    pass

@when("I read the Total Customers card value")
def read_total_customers(dashboard_page):
    dashboard_page.get_total_customers()

@then("the Total Customers card matches the total number of customers in the database")
def total_customers_matches_db(dashboard_page, db_connection):
    total_customers = dashboard_page.get_total_customers()
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM customers")
        db_total_customers = cursor.fetchone()[0]
    print(f"Total Customers from Dashboard: {total_customers}")
    print(f"Total Customers from Database: {db_total_customers}")
    assert total_customers == db_total_customers


# -----  Active Accounts card accuracy ------

@when("I read the Active Accounts card value")
def read_active_accounts(dashboard_page):
    dashboard_page.get_active_accounts()

@then("the Active Accounts card matches the number of active accounts in the database")
def active_accounts_matches_db(dashboard_page, db_connection):
    active_accounts = dashboard_page.get_active_accounts()
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'active'")
        db_active_accounts = cursor.fetchone()[0]
    print(f"Active Accounts from Dashboard: {active_accounts}")
    print(f"Active Accounts from Database: {db_active_accounts}")
    assert active_accounts == db_active_accounts


# -----  Active Loans card accuracy ------
@when("I read the Active Loans card value")
def read_active_loans(dashboard_page):
    dashboard_page.get_active_loans()

@then("the Active Loans card matches the number of active loans in the database")
def active_loans_matches_db(dashboard_page, db_connection):
    active_loans = dashboard_page.get_active_loans()
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM loans WHERE status = 'active'")
        db_active_loans = cursor.fetchone()[0]
    print(f"Active Loans from Dashboard: {active_loans}")
    print(f"Active Loans from Database: {db_active_loans}")
    assert active_loans == db_active_loans
