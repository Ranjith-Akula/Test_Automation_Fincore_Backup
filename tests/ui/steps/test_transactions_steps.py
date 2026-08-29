import pytest
from datetime import datetime
from pytest_bdd import scenarios, given, when, then
from tests.ui.pages.transactions_page import TransactionsPage
from tests.ui.pages.login_page import LoginPage

scenarios("../features/transactions.feature")

#login and go to transactions page
@pytest.fixture
def transactions_page(page, valid_credentials):
    lp = LoginPage(page)
    lp.goto()
    lp.login(valid_credentials["username"], valid_credentials["password"])
    tp = TransactionsPage(page)
    tp.goto()
    return tp

# --- Filter transactions by type--- #
@given("I am on the transactions screen")
def transactions_screen(transactions_page):
    pass

@when('I filter by transaction type "Credit"')
def filter_by_transaction_type(transactions_page):
    transactions_page.filter_transactions(transaction_type="Credit")

@then('all visible transactions show type "Credit"')
def all_visible_transactions_show_type_credit(transactions_page):
    rows = transactions_page.get_transaction_rows()
    for row in rows.all():
        type_cell = row.locator("td:nth-child(4)").text_content().strip().lower()
        assert type_cell == "credit"
    
# --- Filter transactions by date range --- #
@when("I filter transactions between two dates")
def filter_transactions_between_dates(transactions_page):
    transactions_page.filter_transactions(start_date="2023-01-01", end_date="2023-12-31")

@then("all visible transaction dates fall within that range")
def all_visible_transaction_dates_within_range(transactions_page):
    start = datetime.strptime("2023-01-01", "%Y-%m-%d").date()
    end = datetime.strptime("2023-12-31", "%Y-%m-%d").date()
    rows = transactions_page.get_transaction_rows()
    for row in rows.all():
        date_cell = row.locator("td:nth-child(2)").text_content().strip()
        transaction_date = datetime.strptime(date_cell, "%m/%d/%Y, %I:%M:%S %p").date()
        assert start <= transaction_date <= end

# --- Filter transactions by amount range --- #
@when("I filter transactions between a minimum and maximum amount")
def filter_transactions_between_amounts(transactions_page):
    transactions_page.filter_transactions()

@then("all visible transaction amounts fall within that range")
def all_visible_transaction_amounts_within_range(transactions_page):
    min_amount = 0
    max_amount = 1000000
    rows = transactions_page.get_transaction_rows()
    for row in rows.all():
        amount_cell = row.locator("td:nth-child(5)").text_content().strip()
        amount_text = amount_cell.replace(",", "").split()[-1]
        amount = float(amount_text)
        assert min_amount <= amount <= max_amount

# --- Clear filters --- #
@when("I click the Clear button")
def click_clear_button(transactions_page):
    transactions_page.clear_filters()

@then("all filters are reset and all transactions are visible")
def all_filters_reset_and_all_transactions_visible(transactions_page):
    assert transactions_page.are_filters_cleared()
    assert transactions_page.transaction_table.is_visible()
