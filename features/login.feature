Feature: Login Functionality

    Scenario: non loggedin user redirected to login when opening homepage
        Given an anonymous user navigates to ICMS homepage
        Then the login page is displayed

    Scenario: non loggedin user redirected to login when opening any page other than home
        Given an anonymous user navigates to workbasket
        Then the login page is displayed

    Scenario: user sees error when entering invalid credentials
        Given an anonymous user navigates to Login page
        When the user logs in with invalid credentials
        Then the user is presented with an invalid login message

