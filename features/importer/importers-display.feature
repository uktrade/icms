Feature: Importer DIsplay Functionality

    @importer @display @importer-display
    Scenario: can see importer on the importer list page
        Given the user "app-admin" logs in
        Given the importer "Elm Street Imports" is created in the system
        When  the user navigates to "Importer List page"
        And   clicks on "Elm Street Imports" importer name on the importer search results list
        Then  the view "Elm Street Imports" importer page is displayed

    @importer @display @importer-display
    Scenario: can navigate back to list page
        Given the user "app-admin" navigates to Importer display page of "Elm Street Imports"
        When  the user clicks to navigate back to importer list page
        Then  the importer list page is displayed

    @importer @display @importer-display
    Scenario: can see correct importer data
        When  the user "app-admin" navigates to Importer display page of "Elm Street Imports"
        Then  the following Importer display page fields have the values
            | Field         | Value              |
            | Type          | Organisation       |
            | Name          | Elm Street Imports |
            | Region origin | Non-European       |
            | Comments      |                    |
        And   the following Importer display page Current office data is showned
            | Row | Field     | Value           |
            | 1   | Address   | 1428 Elm Street |
            | 1   | Post Code | 43001 DreamLand |
            | 1   | ROI       | None            |
        And   the Importer display page has no no Archived offices
