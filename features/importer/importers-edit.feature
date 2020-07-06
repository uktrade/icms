Feature: Importer Edit

    @importer @edit @importer-edit
    Scenario: User should see correct importer name
        Given import organisation "Best Imports" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Admin Users"
        And "test_user" has "ILB Admin Users:Maintain All" role
        When "test_user" edits importer "Best Imports"
        Then  importer edit fields read as follows
            | Field         | Value              |
            | Type          | Organisation       |
            | Name          | Best Imports       |
            | Comments      |                    |

    @importer @edit @importer-edit
    Scenario: User should see correct importer region
        Given non-European importer "Best Imports" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Admin Users"
        And "test_user" has "ILB Admin Users:Maintain All" role
        When "test_user" edits importer "Best Imports"
        Then  importer edit fields read as follows
            | Field         | Value              |
            | Region origin | Non-European       |
            | Name          | Best Imports       |
            | Comments      |                    |


    @importer @edit @importer-edit
    Scenario: User should see correct importer offices
        Given importer "Hey Ltd" exists
        And importer "Hey Ltd" has an office with address "1428 Elm Street" and postcode "43001"
        And "bren" is logged in
        And "bren" is a member of "ILB Admin Users"
        And "bren" has "ILB Admin Users:Maintain All" role
        When "bren" edits importer "Hey Ltd"
        Then importer edit offices read as follows
            | Row | Field     | Value           |
            | 1   | Address   | 1428 Elm Street |
            | 1   | Post Code | 43001           |
            | 1   | ROI       | None            |


    @importer @edit @importer-edit
    Scenario: User should be able to add multiple offices
        Given importer "Good Imports" exists
        And "test" is logged in
        And "test" is a member of "ILB Admin Users"
        And "test" has "ILB Admin Users:Maintain All" role
        When "test" edits importer "Good Imports"
        And   clicks on add office
        And   enters address "address 1" 
        And   clicks on add office
        And   enters address "address 2"
        And   submits importer edit form
        Then "importer-view" page for importer "Good Imports" is displayed
        Then importer offices read as follows
            | Row | Field     | Value           |
            | 1   | Address   | address 1       |
            | 2   | Address   | address 2       |

    @importer @edit @importer-edit
    Scenario: User should not be able to add an office with no address
        Given importer "Bad Imports" exists
        And "test" is logged in
        And "test" is a member of "ILB Admin Users"
        And "test" has "ILB Admin Users:Maintain All" role
        When "test" edits importer "Bad Imports"
        And  clicks on add office
        And  submits importer edit form
        Then importer edit offices form shows error "Cannot be empty"
