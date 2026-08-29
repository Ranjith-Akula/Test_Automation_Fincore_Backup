class DashboardPage:
    def __init__(self, page):
        self.page = page
        self.total_customers_value = page.get_by_test_id("summary-customers").locator("p").nth(1)
        self.active_accounts_value = page.get_by_test_id("summary-accounts").locator("p").nth(1)
        self.active_loans_value = page.get_by_test_id("summary-loans").locator("p").nth(1)

    def _read_number(self, locator):
        text = locator.text_content().strip()
        return int(text.replace(",", ""))

    def get_total_customers(self):
        return self._read_number(self.total_customers_value)

    def get_active_accounts(self):
        return self._read_number(self.active_accounts_value)

    def get_active_loans(self):
        return self._read_number(self.active_loans_value)