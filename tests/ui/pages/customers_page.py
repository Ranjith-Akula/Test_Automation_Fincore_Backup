import re

class CustomersPage:
    def __init__(self, page):
        self.page = page
        self.customers_nav_link = page.get_by_test_id("nav-customers")
        self.customer_search_input = page.get_by_test_id("customers-search-input")
        self.customer_status_filter = page.get_by_test_id("customers-status-filter")
        self.customer_search_button = page.get_by_test_id("customers-search-btn")
        self.table_rows = page.get_by_test_id("customers-table").locator("tbody tr")
        self.detail_name_heading = page.locator("h3.text-2xl")

    def goto(self):
        self.customers_nav_link.click()
        self.page.wait_for_load_state("networkidle")

    def fill_search(self, customer_name):
        self.customer_search_input.fill(customer_name)

    def search_customer(self, customer_name):
        self.fill_search(customer_name)
        self.customer_search_button.click()

    def filter_by_status(self, status):
        self.customer_status_filter.select_option(status)

    def get_all_names(self):
        return [name.strip() for name in self.table_rows.locator("td:nth-child(2)").all_text_contents()]

    def get_all_statuses(self):
        return [status.strip() for status in self.table_rows.locator("td:nth-child(4)").all_text_contents()]

    def click_row_by_name(self, customer_name):
        row = self.table_rows.filter(has_text=customer_name)
        row.click()

    def click_first_row(self):
        self.table_rows.first.click()

    def get_detail_customer_name(self):
        return self.detail_name_heading.text_content().strip()

    def customer_table_is_visible(self):
        self.table_rows.first.wait_for(timeout=15000)
        return self.table_rows.count() > 0