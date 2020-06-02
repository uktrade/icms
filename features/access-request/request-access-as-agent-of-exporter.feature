Feature: Request Importer/Exporter Access as an Agent for an Exporter Functionality

    Scenario: Request to act as an agent for an exporter - correct fields are visible
        Given The user "app-importer" logs in
        Given the user navigates to "Request Importer/Exporter Access page"
        When  user sets Access Request Type to "Request access to act as an Agent for an Exporter"
        Then  the following fields visibility is set on the act as an importer/exporter form:
            | Field                                                       | Visible |
            | Access Request Type                                         | True    |
            | Organisation name                                           | True    |
            | Organisation address                                        | True    |
            | What are you importing and where are you importing it from? | False   |
            | Agent name                                                  | True    |
            | Agent address                                               | True    |

    Scenario: Request to act as an importer - success
        Given The user "app-importer" logs in
        Given the user navigates to "Request Importer/Exporter Access page"
        When  user requests to act as an agent for an exporter
        Then  a success message is displayed

    Scenario: List pending requests to act as an importer
        Given The user "app-importer" logs in
        Given the user navigates to "Request Importer/Exporter Access page"
        Given there are 0 Pending Access Requests to act as an exporter
        Given user requests to act as an agent for an exporter
        When the user navigates to "Request Importer/Exporter Access page"
        Then there are 1 Pending Access Requests to act as an exporter
