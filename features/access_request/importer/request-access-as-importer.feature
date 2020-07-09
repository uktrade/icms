Feature: Request Importer/Exporter Access as an Importer

    @access-request @importer-access-request
    Scenario: Access Request page should be displayed when navigated to
        When "some_user" logs in
        And navigates to "access:importer:request"
        Then "access:importer:request" page is displayed

    @access-request @importer-access-request
    Scenario: Correct fields should be visible when user requests access as importer
        When "some_user" logs in
        And  navigates to "access:importer:request"
        And  sets access request type to "Request access to act as an Importer"
        Then following fields are visible on access request form
            | Field                                                       | Visible |
            | Access Request Type                                         | True    |
            | Organisation name                                           | True    |
            | Organisation address                                        | True    |
            | What are you importing and where are you importing it from? | True    |
            | Agent name                                                  | False   |
            | Agent address                                               | False   |

    @access-request @importer-access-request
    Scenario: User should see success message when request to act as an importer is complete
        Given "some_user" is logged in
        When  the user requests to act as an importer
        Then  a success message is displayed

    @access-request @importer-access-request
    Scenario: An importer user should see workbasket when request to act as an importer is complete
        Given "theuser" is logged in
        And import organisation "Test Imports" exists
        And "theuser" is a member of importer "Test Imports"
        When  the user requests to act as an importer
        Then  "workbasket" page is displayed

    @access-request @importer-access-request
    Scenario: An exporter user should see workbasket when request to act as an importer is complete
        Given "theuser" is logged in
        And exporter "Test Exports" exists
        And "theuser" is a member of exporter "Test Exports"
        When  the user requests to act as an importer
        Then  "workbasket" page is displayed

    @access-request @importer-access-request
    Scenario: User should see pending access requests
        Given "some_user" is logged in
        When  the user requests to act as an importer
        And navigates to "access:importer:request"
        Then there are 1 pending access requests to act as an importer
