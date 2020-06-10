Feature: Logout Functionality

    @logout
    Scenario: a user can logout from user home page
        Given the user "app-admin" logs in
        When  the user click on logout button
        Then  the login page is displayed
        And   the user is logged out


    @logout
    Scenario: a user can logout by clicking on the top menu logout link
        # thre is no easy way to trigger the menu, we will just navigate to the same url as the link
        Given the user "app-admin" logs in
        When  the user navigates to "logout"
        Then  the login page is displayed
        And   the user is logged out

