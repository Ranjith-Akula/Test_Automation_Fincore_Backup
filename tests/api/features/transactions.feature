Feature: Transaction API Scenarios
    Tests Transaction Data


    Scenario: Get all transactions
        Given I am authenticated
        When I GET "/transactions"
        Then Response is 200
        And total matches DB count

    
    Scenario: Filter by type
        Given I am authenticated
        When I GET "/transactions?type=credit"
        Then All returned records have transaction_type = credit
    

    Scenario Outline: Filter by date range
        Given I am authenticated
        When I GET "/transactions?from_date=<from_date>&to_date=<to_date>"
        Then All returned transaction_dates fall within the range

        Examples:
            | from_date  | to_date    |
            | 2024-01-01 | 2024-12-31 |
            | 2025-01-01 | 2025-12-31 |
    

    Scenario: Filter by amount range
        Given I am authenticated
        When I GET "/transactions?min_amount=100&max_amount=500"
        Then All returned amounts are between 100 and 500


    Scenario: Filter by account
        Given I am authenticated
        When I GET "/transactions?account_id=5"
        Then All returned records belong to account_id 5 verified against DB
