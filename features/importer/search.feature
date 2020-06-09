Feature: Importer Search Functionality

    @importer @search @importer-search
    Scenario: show all status
        Given An importer with status "DRAFT" is created in the system
        And   An importer with status "ARCHIVED" is created in the system
        And   An importer with status "CURRENT" is created in the system
        And   The user "app-user" logs in
        And   the user navigates to "Importer List page"

        When  the user selects to filter importers with status "Any"
        And   submits the import search from

        Then  the importer search results contain "3" results

    @importer @search @importer-search
    Scenario: search by status
        Given An importer with status "DRAFT" is created in the system
        And   An importer with status "ARCHIVED" is created in the system
        And   An importer with status "CURRENT" is created in the system
        And   The user "app-user" logs in
        And   the user navigates to "Importer List page"

        When  the user selects to filter importers with status "draft"
        And   submits the import search from

        Then  the importer search results contain "1" results
        And   the result at row "1" has the name "DRAFT Importer"
        And   the result at row "1" has the status "Draft"


    @importer @search @importer-search
    Scenario: search by status
        Given An importer with status "DRAFT" is created in the system
        And   An importer with status "ARCHIVED" is created in the system
        And   An importer with status "CURRENT" is created in the system
        And   The user "app-user" logs in
        And   the user navigates to "Importer List page"

        When  the user selects to filter importers with status "archived"
        And   submits the import search from

        Then  the importer search results contain "1" results
        And   the result at row "1" has the name "ARCHIVED Importer"
        And   the result at row "1" has the status "Archived"


    @importer @search @importer-search
    Scenario: search by status
        Given An importer with status "DRAFT" is created in the system
        And   An importer with status "ARCHIVED" is created in the system
        And   An importer with status "CURRENT" is created in the system
        And   The user "app-user" logs in
        And   the user navigates to "Importer List page"

        When  the user selects to filter importers with status "current"
        And   submits the import search from

        Then  the importer search results contain "1" results
        And   the result at row "1" has the name "CURRENT Importer"
        And   the result at row "1" has the status "Current"