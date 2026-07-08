Feature: Authentication Scenarios
    Tests Authentication API

    Scenario: Valid Login
        Given A registered user exists
        When I POST valid credentials to "/auth/login"
        Then Response is 200 
        And response contains a JWT token
    

    Scenario: Invalid password
        Given A registered user exists
        When I POST wrong password to "/auth/login"
        Then Response is 401 with an error message
    

    Scenario: Missing credentials
        Given No credentials provided
        When I POST empty body to "/auth/login"
        Then Response is 400 with validation error