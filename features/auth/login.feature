Feature: Login Functionality

    @login
    Scenario: non loggedin user redirected to login when opening homepage
        Given an anonymous user navigates to ICMS homepage
        Then  the login page is displayed

    @login
    Scenario: non loggedin user redirected to login when opening any page other than home
        Given an anonymous user navigates to workbasket
        Then  the login page is displayed

    @login
    Scenario: user sees error when entering invalid credentials
        Given The user "app-user" is created in the system
        Given an anonymous user navigates to Login page
        When  the user "app-user" logs in with invalid credentials
        Then  an invalid login message is visible

    @login
    Scenario: user sees error when entering an invalid user
        Given an anonymous user navigates to Login page
        When  the user "i-dont-exist" logs in with invalid credentials
        Then  an invalid login message is visible

    @login
    Scenario: user is redirected to "user home" page after login
        Given  the user "app-user" logs in
        Then  the "user home" page is displayed
        And   the text "Hi app-user, you are logged in" is visible

    @login
    Scenario: User home page allow logging out
        Given the user "app-user" logs in
        Then  a button with text "Logout" is visible
