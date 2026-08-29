import pytest
from pytest_bdd import scenarios, given, when, then
from tests.ui.pages.customers_page import CustomersPage
from tests.ui.pages.login_page import LoginPage

scenarios("../features/customers.feature")

#login and go to customers page
@pytest.fixture
def customers_page(page, valid_credentials):
    lp = LoginPage(page)
    lp.goto()
    lp.login(valid_credentials["username"], valid_credentials["password"])
    page.wait_for_load_state("networkidle", timeout=60000)
    page.wait_for_selector('[data-testid="nav-customers"]', timeout=60000)
    cp = CustomersPage(page)
    cp.goto()
    return cp

# --- Customer list loads --- #
@given("I am on the customers screen")
def on_customers_screen(customers_page):
    pass

@when("the page loads")
def page_loads(customers_page):
    pass

@then("a table with customer records is visible")
def table_with_customer_records_is_visible(customers_page):
    assert customers_page.customer_table_is_visible()

# --- Search by name --- #
@when("I type a name in the search box")
def type_name_in_search_box(customers_page):
    customers_page.fill_search("John Doe")
    customers_page.search_customer("John Doe")

@then("only matching customers are shown in the table")
def only_matching_customers_are_shown(customers_page):
    names = customers_page.get_all_names()
    assert all("John Doe" in name for name in names)

# --- Filter by status --- #
@when("I select a status from the filter dropdown")
def select_status_from_filter_dropdown(customers_page):
    customers_page.filter_by_status("active")

@then("all visible rows show that status value")
def only_customers_with_selected_status_are_shown(customers_page):
    statuses = customers_page.get_all_statuses()
    assert all("active" in status.lower() for status in statuses)

# --- View customer detail --- #
@when("I click on a customer row")
def click_on_customer_row(customers_page):
    customers_page.click_first_row()

@then("I navigate to that customer's detail page with all fields visible")
def customer_detail_page_is_displayed(customers_page):
    detail_name = customers_page.get_detail_customer_name()
    assert detail_name is not None and len(detail_name) > 0