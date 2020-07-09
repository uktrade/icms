Feature: Request Importer/Exporter Access as an Agent for an Exporter

    @access-request @exporter-access-request
    Scenario: Correct fields should be visible when user requests access as an agent of an importer
        When "som_user" logs in
        And  navigates to "access:exporter:request"
        And  sets Access Request Type to "Request access to act as an Agent for an Exporter"
        Then following fields are visible on access request form
            | Field                                                       | Visible |
            | Access Request Type                                         | True    |
            | Organisation name                                           | True    |
            | Organisation address                                        | True    |
            | Agent name                                                  | True    |
            | Agent address                                               | True    |

    @access-request @exporter-access-request
    Scenario: User should see success message when request to act as an agent of an exporter
        Given "some_user" is logged in
        When  the user requests to act as an agent of an exporter
        Then  a success message is displayed

    @access-request @importer-access-request
    Scenario: An importer agent should see workbasket when request to act as an agent of exporter is complete
        Given "agent user" is logged in
        And import organisation "Test Imports" exists
        And importer "Agents Ltd" exists
        And "Agents Ltd" is an agent of "Test Imports"
        And "agent user" is a member of importer "Agents Ltd"
        When  the user requests to act as an agent of an exporter
        Then  "workbasket" page is displayed

    @access-request @exporter-access-request
    Scenario: User should see pending access requets
        Given "some_user" is logged in
        When  the user requests to act as an agent of an exporter 
        And navigates to "access:exporter:request"
        Then there are 1 pending access requests to act as an exporter
