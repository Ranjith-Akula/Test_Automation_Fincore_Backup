class TransactionsPage:
    def __init__(self, page):
        self.page = page
        self.transactions_nav_link = page.get_by_test_id("nav-transactions")
        self.transactions_filter_alltypes = page.get_by_test_id("filter-type")
        self.transactions_filter_status = page.get_by_test_id("filter-status")
        self.transactions_from_date = page.get_by_test_id("filter-from-date")
        self.transaction_to_date = page.get_by_test_id("filter-to-date")
        self.transaction_apply_filter_button = page.get_by_test_id("apply-filters-btn")
        self.transaction_clear_button = page.get_by_test_id("clear-filters-btn")
        self.transaction_table = page.get_by_test_id("transactions-table")


    def goto(self):
        self.page.goto("/transactions")
        self.page.get_by_test_id("transactions-page").wait_for()

    def filter_transactions(
        self,
        transaction_type=None,
        status=None,
        from_date=None,
        to_date=None,
        start_date=None,
        end_date=None,
    ):
        # Support both naming styles used by existing step definitions.
        from_date = from_date or start_date
        to_date = to_date or end_date

        if transaction_type:
            self.transactions_filter_alltypes.select_option(transaction_type)
        if status:
            self.transactions_filter_status.select_option(status)
        if from_date:
            self.transactions_from_date.fill(from_date)
        if to_date:
            self.transaction_to_date.fill(to_date)
        self.transaction_apply_filter_button.click()

    def clear_filters(self):
        self.transaction_clear_button.click()
        self.transactions_filter_alltypes.select_option("")
        self.transactions_filter_status.select_option("")
        self.transactions_from_date.fill("")
        self.transaction_to_date.fill("")
        self.transaction_apply_filter_button.click()

    def get_transaction_rows(self):
        return self.transaction_table.locator("tbody tr")

    def are_filters_cleared(self):
        return (self.transactions_filter_alltypes.input_value() == "" and
                self.transactions_filter_status.input_value() == "" and
                self.transactions_from_date.input_value() == "" and
                self.transaction_to_date.input_value() == "")
    