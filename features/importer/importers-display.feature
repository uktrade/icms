Feature: Importer Display

    @importer @display @importer-display
    Scenario: User in ILB Admin Users with "Maintain All" role should be able to view importer in the importer list
        Given importer "Elm Street Imports" exists
        Given "Roy" is logged in
        And "Roy" is a member of "ILB Admin Users"
        And "Roy" has "ILB Admin Users:Maintain All" role
        When "Roy" navigates to "importer-list"
        Then importer "Elm Street Imports" is in the list

    @importer @display @importer-display
    Scenario: User should see importer details when importer name is clicked
        Given importer "Elm Street Imports" exists
        And "John" is logged in
        And "John" is a member of "ILB Admin Users"
        And "John" has "ILB Admin Users:Maintain All" role
        When "John" navigates to "importer-list"
        And  clicks on importer name "Elm Street Imports"
        Then "importer-view" page for importer "Elm Street Imports" is displayed
        And context header reads "View Importer - Elm Street Imports" 
        And importer name reads "Elm Street Imports"

    @importer @display @importer-display
    Scenario: User should be able to navigate back
        Given importer "Elm Street Imports" exists
        And "Ashley" is logged in
        And "Ashley" is a member of "ILB Admin Users"
        And "Ashley" has "ILB Admin Users:Maintain All" role
        When "Ashley" views importer "Elm Street Imports"
        And  clicks on the back link
        Then "importer-list" page is displayed

    @importer @display @importer-display
    Scenario: User should see correct importer name 
        Given import organisation "Elm Street Imports" exists
        And "bren" is logged in
        And "bren" is a member of "ILB Admin Users"
        And "bren" has "ILB Admin Users:Maintain All" role
        When "bren" views importer "Elm Street Imports"
        Then importer details read as follows
            | Field         | Value              |
            | Type          | Organisation       |
            | Name          | Elm Street Imports |
            | Comments      |                    |

    @importer @display @importer-display
    Scenario: User should see correct importer region origin 
        Given non-European importer "US Imports" exists
        And "bren" is logged in
        And "bren" is a member of "ILB Admin Users"
        And "bren" has "ILB Admin Users:Maintain All" role
        When "bren" views importer "US Imports"
        Then importer details read as follows
            | Field         | Value              |
            | Name          | US Imports         |
            | Region origin | Non-European       |
            | Comments      |                    |

    @importer @display @importer-display
    Scenario: User should see correct importer offices
        Given importer "Hey Ltd" exists
        And importer "Hey Ltd" has an office with address "1428 Elm Street" and postcode "43001"
        And "bren" is logged in
        And "bren" is a member of "ILB Admin Users"
        And "bren" has "ILB Admin Users:Maintain All" role
        When "bren" views importer "Hey Ltd"
        Then importer offices read as follows
            | Row | Field     | Value           |
            | 1   | Address   | 1428 Elm Street |
            | 1   | Post Code | 43001           |
            | 1   | ROI       | None            |
        And no archived importer office is displayed
