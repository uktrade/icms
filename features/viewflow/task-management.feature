@skip
Feature: Viewflow Task Management

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

