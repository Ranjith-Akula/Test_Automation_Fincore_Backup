Feature: Login
    As a user
    I want to login to fincore portal
    So that I can access my customer, transaction and loan data


    Scenario: Valid login
        Given I am on the login page
        When I enter valid credentials and click login
        Then I am redirected to the dashboard

    
    Scenario: Invalid password
        Given I am on the login page
        When I enter wrong password and click login
        Then an error message is displayed on screen

    
    Scenario: Empty form submission
        Given I am on the login page
        When I click login without entering anything
        Then validation messages appear for both fields
    

    Scenario: Logout
        Given I am logged into the portal
        When I click the logout button
        Then I am redirected back to the login page
