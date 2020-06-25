Feature: Importer Edit Functionality

    @importer @edit @importer-edit
    Scenario: can see correct importer data
        When  the user "app-admin" navigates to Importer edit page of "Elm Street Imports"
        Then  the following Importer edit page fields have the values
            | Field         | Value              |
            | Type          | Organisation       |
            | Name          | Elm Street Imports |
            | Region origin | Non-European       |
            | Comments      |                    |
        And   the following Importer edit page office data is showned
            | Row | Field     | Value           |
            | 1   | Status    | Current         |
            | 1   | Address   | 1428 Elm Street |
            | 1   | Post Code | 43001 DreamLand |
            | 1   | ROI       | None            |

    @importer @edit @importer-edit
    Scenario: can add multiple addresses
        Given the user "app-admin" navigates to Importer edit page of "Elm Street Imports"
        When  the user clicks on add office
        And   the user enters "address 1" in the new office address fields
        And   the user clicks on add office
        And   the user enters "address 2" in the new office address fields
        And   the user submits the importer edit form

        Then  the user is redirected to the importer display page of "Elm Street Imports"
        And   the following Importer display page Current office data is showned
            | Row | Field     | Value           |
            | 1   | Address   | 1428 Elm Street |
            | 1   | Post Code | 43001 DreamLand |
            | 1   | ROI       | None            |
            | 2   | Address   | address 1       |
            | 3   | Address   | address 2       |

    @importer @edit @importer-edit
    Scenario: cannot add empty address
    Given the user "app-admin" navigates to Importer edit page of "Elm Street Imports"
    When  the user clicks on add office
    And   the user submits the importer edit form
    Then  the Importer edit page office form shows an error on the address field
