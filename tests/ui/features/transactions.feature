Feature: Transactions
    As a user,
    I want to view the transactions page after logging in,
    so that I can access the transaction information of the application.

    Scenario: Filter by type
        Given I am on the transactions screen
        When I filter by transaction type "Credit"
        Then all visible transactions show type "Credit"
    
    Scenario: Filter by date range
        Given I am on the transactions screen
        When I filter transactions between two dates
        Then all visible transaction dates fall within that range
    
    Scenario: Clear filters
        Given I am on the transactions screen
        When I click the Clear button
        Then all filters are reset and all transactions are visible