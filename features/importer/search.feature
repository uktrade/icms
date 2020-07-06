Feature: Importer Search

    @importer @403 @search @importer-search
    Scenario: User without access shouldn't see the list
        When "someone" logs in
        And  navigates to "importer-list"
        Then 403 error page is displayed

    @importer @search @importer-search
    Scenario: Users should see all active and archived importers
        Given archived importer "Old Toby Imports Ltd" exists
        And importer "Longbottom Imports" exists
        And "Saruman" is logged in
        And "Saruman" is a member of "ILB Admin Users"
        And "Saruman" has "ILB Admin Users:Maintain All" role
        When  "Sauron" navigates to "importer-list"
        And  filters importers by status "Any"
        Then importer search has "2" results


    @importer @search @importer-search
    Scenario: User should only see archived importers if filtered by archived
        Given archived importer "Dissolved Importers Ltd" exists
        And   importer "Agile Importers" exists
        And   "an admin" is logged in
        And   "an admin" is a member of "ILB Admin Users"
        And   "an admin" has "ILB Admin Users:Maintain All" role
        When  "an admin" navigates to "importer-list"
        And   filters importers by status "Archived"
        Then  importer search has "1" results
        And   importer name at row "1" is "Dissolved Importers Ltd"
        And   importer status at row "1" is "Archived"

    @importer @search @importer-search
    Scenario: User should only see active importers if filtered by current
        Given archived importer "Dissolved Importers Ltd" exists
        And   importer "Agile Importers" exists
        And   "an admin" is logged in
        And   "an admin" is a member of "ILB Admin Users"
        And   "an admin" has "ILB Admin Users:Maintain All" role
        When  "an admin" navigates to "importer-list"
        And   filters importers by status "Current"
        Then  importer search has "1" results
        And   importer name at row "1" is "Agile Importers"
        And   importer status at row "1" is "Current"

    @importer @search @importer-search
    Scenario: User should see correct actions with archived importer
        Given archived importer "Dissolved Importers Ltd" exists
        And   "an admin" is logged in
        And   "an admin" is a member of "ILB Admin Users"
        And   "an admin" has "ILB Admin Users:Maintain All" role
        When  "an admin" navigates to "importer-list"
        Then   importer at row "1" has action "unarchive"
        And   importer at row "1" has action "create agent"
        And   importer at row "1" has action "edit"

    @importer @search @importer-search
    Scenario: User should see correct actions with active importer
        Given importer "Agile Importers Ltd" exists
        And   "an admin" is logged in
        And   "an admin" is a member of "ILB Admin Users"
        And   "an admin" has "ILB Admin Users:Maintain All" role
        When  "an admin" navigates to "importer-list"
        Then   importer at row "1" has action "archive"
        And   importer at row "1" has action "create agent"
        And   importer at row "1" has action "edit"
