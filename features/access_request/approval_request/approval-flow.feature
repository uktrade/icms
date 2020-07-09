Feature: Approval Request Flow

    @approval-request @run
    Scenario: Importer user should see workbasket after responding to approval request
        Given "test_user" is logged in
        And import organisation "Big Imports" exists
        And "test_user" is a member of importer "Big Imports"
        And "test_user" has approver role for importer "Big Imports"
        And "test_user" has permission "view_approvalrequestprocess"
        And an approval request "respond" task owned by "test_user" exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And clicks on button "Respond"
        Then "workbasket" page is displayed
