Feature: Login Functionality

    Scenario: non loggedin user redirected to login when opening homepage
        Given an anonymous user navigates to ICMS homepage
        Then the login page is displayed

    Scenario: non loggedin user redirected to login when opening any page other than home
        Given an anonymous user navigates to workbasket
        Then the login page is displayed

    Scenario: user sees error when entering invalid credentials
        Given The user "app-user" is created in the system
        Given an anonymous user navigates to Login page
        When the user "app-user" logs in with invalid credentials
        Then an invalid login message is visible

