Feature: Request Importer/Exporter Access as an Importer

    @access-request
    Scenario: Access Request page should be displayed when navigated to
        When "some_user" logs in
        And navigates to "access:request"
        Then "access:request" page is displayed

    @access-request
    Scenario: Correct fields should be visible when user requests access as importer
        When "some_user" logs in
        And  navigates to "access:request"
        And  sets Access Request Type to "Request access to act as an Importer"
        Then following fields are visible on access request form
            | Field                                                       | Visible |
            | Access Request Type                                         | True    |
            | Organisation name                                           | True    |
            | Organisation address                                        | True    |
            | What are you importing and where are you importing it from? | True    |
            | Agent name                                                  | False   |
            | Agent address                                               | False   |

    @access-request
    Scenario: User should see success message when request to act as an importer is complete
        Given "some_user" is logged in
        When  the user requests to act as an importer
        Then  a success message is displayed

    @access-request
    Scenario: User should see pending access requets
        Given "some_user" is logged in
        When  the user requests to act as an importer
        And navigates to "access:request"
        Then there are 1 pending access requests to act as an importer
