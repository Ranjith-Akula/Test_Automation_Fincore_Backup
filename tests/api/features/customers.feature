Feature: Customer API Scenarios
  Tests Customer Data

  Scenario: Get all customers
    Given I am authenticated
    When I GET "/customers"
    Then Response is 200
    And data array is non-empty
    And total matches DB count

  Scenario: Filter active customers
    Given I am authenticated
    When I GET "/customers?status=active"
    Then All returned records have status = active

  Scenario: Search by name
    Given I am authenticated
    When I GET "/customers?search=JOHN"
    Then All returned names contain JOHN

  Scenario: Get customer by ID
    Given I am authenticated
    When I GET "/customers/1"
    Then Response contains customer with id=1 matching DB record

  Scenario: Invalid customer ID
    Given I am authenticated
    When I GET "/customers/99999"
    Then Response is 404 with error message

  Scenario: No auth token
    Given I am not authenticated
    When I GET "/customers"
    Then Response is 401