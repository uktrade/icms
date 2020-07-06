Feature: Logout

    @logout
    Scenario: a user can logout from user home page
        Given "app-admin" is logged in
        When  the user clicks on logout button
        Then  "login" page is displayed
        And   the user is logged out


    @logout
    Scenario: user gets logged out if navigated to /logout 
        # thre is no easy way to trigger the menu, we will just navigate to the same url as the link
        Given "app-admin" is logged in
        When  the user navigates to "logout"
        Then  "login" page is displayed
        And   the user is logged out

