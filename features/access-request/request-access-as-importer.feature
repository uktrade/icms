Feature: Request Importer/Exporter Access as an Importer Functionality

    @access-request
    Scenario: Request import access page is displayed
        Given The user "app-importer" logs in
        When the user navigates to "Request Importer/Exporter Access page"
        Then  Request Importer/Exporter Access page is displayed

    @access-request
    Scenario: Request to act as an importer - correct fields are visible
        Given The user "app-importer" logs in
        Given the user navigates to "Request Importer/Exporter Access page"
        When  user sets Access Request Type to "Request access to act as an Importer"
        Then  the following fields visibility is set on the act as an importer/exporter form:
            | Field                                                       | Visible |
            | Access Request Type                                         | True    |
            | Organisation name                                           | True    |
            | Organisation address                                        | True    |
            | What are you importing and where are you importing it from? | True    |
            | Agent name                                                  | False   |
            | Agent address                                               | False   |

    @access-request
    Scenario: Request to act as an importer - success
        Given The user "app-importer" logs in
        Given the user navigates to "Request Importer/Exporter Access page"
        When  user requests to act as an importer
        Then  a success message is displayed

    @access-request
    Scenario: List pending requests to act as an importer
        Given The user "app-importer" logs in
        Given the user navigates to "Request Importer/Exporter Access page"
        Given there are 0 Pending Access Requests to act as an importer
        Given user requests to act as an importer
        When the user navigates to "Request Importer/Exporter Access page"
        Then there are 1 Pending Access Requests to act as an importer
