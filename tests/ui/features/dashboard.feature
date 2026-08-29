Feature: Dashboard
    As a user, 
    I want to view the dashboard after logging in, 
    so that I can access the main features of the application.


    Scenario: Total Customers card accuracy
        Given I am on the dashboard
        When I read the Total Customers card value
        Then the Total Customers card matches the total number of customers in the database

    Scenario: Active Accounts card accuracy
        Given I am on the dashboard
        When I read the Active Accounts card value
        Then the Active Accounts card matches the number of active accounts in the database
    
    Scenario: Active Loans card accuracy
        Given I am on the dashboard
        When I read the Active Loans card value
        Then the Active Loans card matches the number of active loans in the database

