Feature: customers
    As a user,
    I want to view the customers page after logging in,
    so that I can access the customer information of the application.

    Scenario: Customer list loads
        Given I am on the customers screen
        When the page loads
        Then a table with customer records is visible

    Scenario: Search by name
        Given I am on the customers screen
        When I type a name in the search box
        Then only matching customers are shown in the table

    Scenario: Filter by status
        Given I am on the customers screen
        When I select a status from the filter dropdown
        Then all visible rows show that status value
    
    Scenario: View customer detail
        Given I am on the customers screen
        When I click on a customer row
        Then I navigate to that customer's detail page with all fields visible