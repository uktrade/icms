Feature: Request Importer/Exporter Access as an Exporter

    @access-request @exporter-access-request
    Scenario: Correct fields should be visible when user requests access as exporter
        When "som_user" logs in
        And  navigates to "access:exporter:request"
        And  sets access request type to "Request access to act as an Exporter"
        Then following fields are visible on access request form
            | Field                | Visible |
            | Access Request Type  | True    |
            | Organisation name    | True    |
            | Organisation address | True    |
            | Agent name           | False   |
            | Agent address        | False   |

    @access-request @exporter-access-request
    Scenario: User should see success message when request to act as an exporter is complete
        Given "some_user" is logged in
        When  the user requests to act as an exporter
        Then  a success message is displayed


    @access-request @exporter-access-request
    Scenario: An importer user should see workbasket when request to act as an exporter is complete
        Given "theuser" is logged in
        And import organisation "Test Imports" exists
        And "theuser" is a member of importer "Test Imports"
        When  the user requests to act as an exporter
        Then  "workbasket" page is displayed

    @access-request @exporter-access-request
    Scenario: An exporter user should see workbasket when request to act as an exporter is complete
        Given "theuser" is logged in
        And exporter "Test Exports" exists
        And "theuser" is a contact of exporter "Test Exports"
        When  the user requests to act as an exporter
        Then  "workbasket" page is displayed

    @access-request @exporter-access-request
    Scenario: User should see pending access requets
        Given "some_user" is logged in
        When  the user requests to act as an exporter
        And navigates to "access:exporter:request"
        Then there are 1 pending access requests to act as an exporter
