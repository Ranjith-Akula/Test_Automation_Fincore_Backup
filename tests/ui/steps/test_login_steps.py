import re
import pytest
from pytest_bdd import scenarios, given, when, then
from playwright.sync_api import expect
from tests.ui.pages.login_page import LoginPage

scenarios("../features/login.feature")


@pytest.fixture
def login_page(page):
    lp = LoginPage(page)
    lp.goto()
    return lp

# ------------ Valid Login ------------

@given("I am on the login page")
def on_login_page(login_page):
    pass

@when("I enter valid credentials and click login")
def enter_valid_credentials(login_page, valid_credentials):
    login_page.login(valid_credentials["username"], valid_credentials["password"])

@then("I am redirected to the dashboard")
def redirected_to_dashboard(page):
    expect(page).to_have_url(re.compile(r".*/dashboard$"))


# --- ---------- Invalid Login ------------

@when("I enter wrong password and click login")
def enter_wrong_pwd(login_page, valid_credentials):
    login_page.login(valid_credentials["username"], "wrongpassword", wait_for_success=False)

@then("an error message is displayed on screen")
def error_message_displayed(login_page):
    expect(login_page.error_message).to_be_visible()


# ----------- Empty Fields ------------

@when("I click login without entering anything")
def click_login_empty(login_page):
    login_page.submit_empty()

@then("validation messages appear for both fields")
def validation_messages_shown(login_page):
    assert login_page.username_is_invalid()
    assert login_page.password_is_invalid()

# ----------- Logout ------------

@given("I am logged into the portal")
def logged_into_portal(login_page, valid_credentials):
    login_page.login(valid_credentials["username"], valid_credentials["password"])
    expect(login_page.page).to_have_url(re.compile(r".*/dashboard$"))

@when("I click the logout button")
def click_logout(login_page):
    login_page.logout()

@then("I am redirected back to the login page")
def redirected_to_login(page):
    expect(page).to_have_url(re.compile(r".*/login$"))
