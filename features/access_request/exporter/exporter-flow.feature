Feature: Exporter Access Request Flow

    @access-request @exporter-access-request
    Scenario: Export case officers should see link exporter task after request
        Given "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Certificate Application Case Officer" role
        And "test_user" has permission "view_exporteraccessrequestprocess"
        When the user requests to act as an exporter
        And navigates to "workbasket"
        And clicks on link "Resume Task"
        Then section title "Link Exporter" is visible

    @access-request @exporter-access-request
    Scenario: Export case officers should see review task after link exporter
        Given import organisation "Some Ltd" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Certificate Application Case Officer" role
        And "test_user" has permission "view_exporteraccessrequestprocess"
        And an exporter access request "link_exporter" task owned by "test_user" exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And clicks on button "Link Exporter"
        Then section title "Review" is visible

    @access-request @exporter-access-request
    Scenario: Export case officers should see link exporter when relink exporter action is taken
        Given import organisation "Some Ltd" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Certificate Application Case Officer" role
        And "test_user" has permission "view_exporteraccessrequestprocess"
        And an exporter access request "review" task owned by "test_user" exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And clicks on button "Relink exporter"
        Then section title "Link Exporter" is visible

    @access-request @exporter-access-request
    Scenario: Export case officers should see close request task after clicking Proceed to Close
        Given import organisation "Pal Ltd" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Certificate Application Case Officer" role
        And "test_user" has permission "view_exporteraccessrequestprocess"
        And an exporter access request "review" task owned by "test_user" exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And clicks on button "Proceed to Close"
        And clicks on button "OK"
        Then section title "Close Request" is visible
        And button "Close Request" is visible

    @access-request @exporter-access-request
    Scenario: Export case officers should see review when restart approval action is taken
        Given import organisation "Pal Ltd" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Certificate Application Case Officer" role
        And "test_user" has permission "view_exporteraccessrequestprocess"
        And an exporter access request "close_request" task owned by "test_user" exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And clicks on button "Restart exporter Access Approval"
        Then section title "Review" is visible

    @access-request @exporter-access-request
    Scenario: Export case officers should see workbasket after closing request
        Given import organisation "Pal Ltd" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Certificate Application Case Officer" role
        And "test_user" has permission "view_exporteraccessrequestprocess"
        And an exporter access request "close_request" task owned by "test_user" exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And sets access request close response to "Approved"
        And clicks on button "Close Request"
        And clicks on button "OK"
        Then "workbasket" page is displayed

    @access-request @exporter-access-request
    Scenario: Export case officers should see workbasket after starting approval
        Given import organisation "Pal Ltd" exists
        And "test_user" is logged in
        And "test_user" is a member of "ILB Case Officers"
        And "test_user" has "ILB Case Officers:Certificate Application Case Officer" role
        And "test_user" has permission "view_exporteraccessrequestprocess"
        And an exporter access request "review" task owned by "test_user" exists
        When "test_user" navigates to "workbasket"
        And clicks on link "Resume Task"
        And clicks on button "Start exporter Access Approval"
        And clicks on button "OK"
        Then "workbasket" page is displayed

