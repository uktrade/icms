Feature: Importer Access Request Flow

    @access-request @importer-access-request
    Scenario: Import case officers should see link importer task after request
        Given "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Import Application Case Officer" role
        And "test_user" has permission "view_importeraccessrequestprocess"
        When the user requests to act as an importer
        And navigates to "workbasket"
        And clicks on link "Resume Task"
        Then section title "Link Importer" is visible

    @access-request @importer-access-request
    Scenario: Import case officers should see review task after link importer
        Given import organisation "Some Ltd" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Import Application Case Officer" role
        And "test_user" has permission "view_importeraccessrequestprocess"
        And an importer access request "link_importer" task owned by "test_user" exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And clicks on button "Link Importer"
        Then section title "Review" is visible

    @access-request @importer-access-request
    Scenario: Import case officers should see link importer when relink importer action is taken
        Given import organisation "Some Ltd" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Import Application Case Officer" role
        And "test_user" has permission "view_importeraccessrequestprocess"
        And an importer access request "review" task owned by "test_user" exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And clicks on button "Relink importer"
        Then section title "Link Importer" is visible

    @access-request @importer-access-request
    Scenario: Import case officers should see close request task after clicking Proceed to Close
        Given import organisation "Pal Ltd" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Import Application Case Officer" role
        And "test_user" has permission "view_importeraccessrequestprocess"
        And an importer access request "review" task owned by "test_user" exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And clicks on button "Proceed to Close"
        And clicks on button "OK"
        Then section title "Close Request" is visible
        And button "Close Request" is visible

    @access-request @importer-access-request
    Scenario: Import case officers should see review when restart approval action is taken
        Given import organisation "Pal Ltd" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Import Application Case Officer" role
        And "test_user" has permission "view_importeraccessrequestprocess"
        And an importer access request "close_request" task owned by "test_user" exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And clicks on button "Restart importer Access Approval"
        Then section title "Review" is visible

    @access-request @importer-access-request
    Scenario: Import case officers should see workbasket after closing request
        Given import organisation "Pal Ltd" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Import Application Case Officer" role
        And "test_user" has permission "view_importeraccessrequestprocess"
        And an importer access request "close_request" task owned by "test_user" exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And sets access request close response to "Approved"
        And clicks on button "Close Request"
        And clicks on button "OK"
        Then "workbasket" page is displayed

    @access-request @importer-access-request
    Scenario: Import case officers should see workbasket after starting approval
        Given import organisation "Pal Ltd" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Import Application Case Officer" role
        And "test_user" has permission "view_importeraccessrequestprocess"
        And an importer access request "review" task owned by "test_user" exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And clicks on button "Start importer Access Approval"
        And clicks on button "OK"
        Then "workbasket" page is displayed

