Feature: Login Functionality

    Scenario: non loggedin user redirected to login when opening homepage
        Given an anonymous user navigates to ICMS homepage
        Then  the login page is displayed

    Scenario: non loggedin user redirected to login when opening any page other than home
        Given an anonymous user navigates to workbasket
        Then  the login page is displayed

    Scenario: user sees error when entering invalid credentials
        Given The user "app-user" is created in the system
        Given an anonymous user navigates to Login page
        When  the user "app-user" logs in with invalid credentials
        Then  an invalid login message is visible

    Scenario: user is redirected to "user home" page after login
        Given  the user "app-user" logs in
        Then  the "user home" page is displayed
        And   the text "Hi app-user, you are logged in" is visible

    Scenario: User home page allow logging out
        Given the user "app-user" logs in
        Then  a button with text "Logout" is visible
