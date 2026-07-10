Feature: Loan API Scenarios
    Test Loan Data


    Scenario: Get all loans
        Given I am authenticated
        When I GET "/loans"
        Then Response is 200
        And total matches DB count
    

    Scenario: Filter by status
        Given I am authenticated
        When I GET "/loans?status=active"
        Then All returned loans have status = active

    
    Scenario: Get loan by ID
        Given I am authenticated
        When I GET "/loans/1"
        Then All fields present including loan_duration_days and emi_amount


    Scenario: Verify computed fields
        Given I am authenticated
        When I GET "/loans/1"
        Then loan_duration_days matches end_date minus start_date calculation
    

    Scenario: Dashboard summary
        Given I am authenticated
        When I GET "/dashboard/summary"
        Then total_customers match DB counts
        And active_loans match DB counts