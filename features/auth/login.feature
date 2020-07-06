Feature: Login

    @login
    Scenario: anonymous users are redirected to login when accessing homepage
        When an anonymous user navigates to "home"
        Then  "login" page is displayed

    @login
    Scenario: anonymous user is redirected to login when accessing workbasket
        When an anonymous user navigates to "workbasket"
        Then  "login" page is displayed

    @login
    Scenario: user sees invalid credentials error message
        Given user "John" exists
        When  "John" attempts login with invalid credentials
        Then  an invalid credentials message is displayed

    @login
    Scenario: user sees error message with invalid username
        When  "a ghost" attempts login
        Then  an invalid credentials message is displayed

    @login
    Scenario: user is redirected to home page after login
        When "test" logs in
        Then "home" page is displayed

