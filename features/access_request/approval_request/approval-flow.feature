@skip
Feature: Approval Request Flow

    @approval-request
    Scenario: Importer user should see workbasket after responding approve
        Given "test_user" is logged in
        And import organisation "Big Imports" exists
        And "test_user" is a member of importer "Big Imports"
        And "test_user" has approver role for importer "Big Imports"
        And "test_user" has permission "view_approvalrequestprocess"
        And approval request to importer "Big Imports" exists for user "test_user"
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And sets approval request response to "Approve"
        And clicks on button "Send Response"
        And clicks on button "OK"
        Then "workbasket" page is displayed

    @approval-request
    Scenario: Importer user should see workbasket after responding refuse
        Given "test_user" is logged in
        And import organisation "Big Imports" exists
        And "test_user" is a member of importer "Big Imports"
        And "test_user" has approver role for importer "Big Imports"
        And "test_user" has permission "view_approvalrequestprocess"
        And approval request to importer "Big Imports" exists for user "test_user"
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And sets approval request response to "Refuse"
        And clicks on button "Send Response"
        And clicks on button "OK"
        Then "workbasket" page is displayed

    @access-request-link @importer-access-request
    Scenario: user should see take ownership action of unassigned task
        Given "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Import Application Case Officer" role
        And "test_user" has permission "view_importeraccessrequestprocess"
        And an importer access request task exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        Then button "Take Ownership" is visible
