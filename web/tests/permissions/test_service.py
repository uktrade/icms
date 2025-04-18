import pytest
from guardian.shortcuts import remove_perm

from web.flow.models import ProcessTypes
from web.models import Constabulary, Report, User
from web.permissions.perms import Perms
from web.permissions.service import (
    AppChecker,
    can_user_edit_firearm_authorities,
    can_user_edit_org,
    can_user_edit_section5_authorities,
    can_user_manage_org_contacts,
    can_user_view_org,
    can_user_view_report,
    can_user_view_search_cases,
    constabulary_add_contact,
    constabulary_get_contacts,
    constabulary_remove_contact,
    filter_users_with_org_access,
    get_all_case_officers,
    get_case_officers_for_process_type,
    get_ilb_case_officers,
    get_org_obj_permissions,
    get_report_permission,
    get_report_type_for_permission,
    get_sanctions_case_officers,
    get_user_exporter_permissions,
    get_user_importer_permissions,
    get_users_with_permission,
    is_user_agent_of_org,
    is_user_org_admin,
    organisation_add_contact,
    organisation_get_contacts,
    organisation_remove_contact,
)
from web.reports.constants import ReportType


class TestPermissionsService:
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        importer,
        exporter,
        agent_importer,
        agent_exporter,
        importer_one_contact,
        importer_one_agent_one_contact,
        exporter_one_contact,
        exporter_one_agent_one_contact,
        ilb_admin_user,
        nca_admin_user,
        export_search_user,
        import_search_user,
        fa_sil_app,
        fa_sil_agent_app,
        com_app,
        com_agent_app,
    ):
        self.importer = importer
        self.agent_importer = agent_importer
        self.exporter = exporter
        self.agent_exporter = agent_exporter
        self.importer_contact = importer_one_contact
        self.importer_agent_contact = importer_one_agent_one_contact
        self.exporter_contact = exporter_one_contact
        self.exporter_agent_contact = exporter_one_agent_one_contact
        self.ilb_admin = ilb_admin_user
        self.nca_admin = nca_admin_user
        self.export_search_user = export_search_user
        self.import_search_user = import_search_user

        self.fa_sil_app = fa_sil_app
        self.fa_sil_agent_app = fa_sil_agent_app
        self.com_app = com_app
        self.com_agent_app = com_agent_app

    def test_app_checker(self):
        importer_checker = AppChecker(self.importer_contact, self.fa_sil_app)
        importer_agent_checker = AppChecker(self.importer_agent_contact, self.fa_sil_agent_app)
        export_checker = AppChecker(self.exporter_contact, self.com_app)
        export_agent_checker = AppChecker(self.exporter_agent_contact, self.com_agent_app)
        ilb_admin_import_checker = AppChecker(self.ilb_admin, self.fa_sil_app)
        ilb_admin_export_checker = AppChecker(self.ilb_admin, self.com_app)
        nca_admin_import_checker = AppChecker(self.nca_admin, self.fa_sil_app)
        nca_admin_export_checker = AppChecker(self.nca_admin, self.com_app)
        import_search_import_checker = AppChecker(self.import_search_user, self.fa_sil_app)
        import_search_export_checker = AppChecker(self.import_search_user, self.com_app)
        export_search_import_checker = AppChecker(self.export_search_user, self.fa_sil_app)
        export_search_export_checker = AppChecker(self.export_search_user, self.com_app)

        #
        # Check importer, exporter and agent apps have correct access
        #
        assert importer_checker.can_edit()
        assert importer_checker.can_view()
        assert importer_checker.can_vary()

        assert importer_agent_checker.can_edit()
        assert importer_agent_checker.can_view()
        assert importer_agent_checker.can_vary()

        assert export_checker.can_edit()
        assert export_checker.can_view()
        assert export_checker.can_vary()

        assert export_agent_checker.can_edit()
        assert export_agent_checker.can_view()
        assert export_agent_checker.can_vary()

        #
        # Test ILB admin access (They can't edit applications)
        #
        assert not ilb_admin_import_checker.can_edit()
        assert ilb_admin_import_checker.can_view()
        assert ilb_admin_import_checker.can_vary()

        assert not ilb_admin_export_checker.can_edit()
        assert ilb_admin_export_checker.can_view()
        assert ilb_admin_export_checker.can_vary()

        #
        # Check import and export contacts do not have permission for the other's app.
        #
        importer_checker = AppChecker(self.importer_contact, self.com_app)
        export_checker = AppChecker(self.exporter_contact, self.fa_sil_app)

        assert not importer_checker.can_edit()
        assert not importer_checker.can_view()
        assert not importer_checker.can_vary()

        assert not export_checker.can_edit()
        assert not export_checker.can_view()
        assert not export_checker.can_vary()

        #
        # Test NCA admin access (They can only view import applications)
        #
        assert not nca_admin_import_checker.can_edit()
        assert nca_admin_import_checker.can_view()
        assert not nca_admin_import_checker.can_vary()

        assert not nca_admin_export_checker.can_edit()
        assert not nca_admin_export_checker.can_view()
        assert not nca_admin_export_checker.can_vary()

        #
        # Test Import Search User access (They can only view import applications)
        #
        assert not import_search_import_checker.can_edit()
        assert import_search_import_checker.can_view()
        assert not import_search_import_checker.can_vary()

        assert not import_search_export_checker.can_edit()
        assert not import_search_export_checker.can_view()
        assert not import_search_export_checker.can_vary()

        #
        # Test Export Search User access (They can only view export applications)
        #
        assert not export_search_import_checker.can_edit()
        assert not export_search_import_checker.can_view()
        assert not export_search_import_checker.can_vary()

        assert not export_search_export_checker.can_edit()
        assert export_search_export_checker.can_view()
        assert not export_search_export_checker.can_vary()

    def test_can_user_edit_firearm_authorities(self):
        #
        # ILB admins have the "edit_firearm_authorities" permission
        #
        assert can_user_edit_firearm_authorities(self.ilb_admin)

        #
        # Applicants do not
        #
        assert not can_user_edit_firearm_authorities(self.importer_contact)
        assert not can_user_edit_firearm_authorities(self.importer_agent_contact)
        assert not can_user_edit_firearm_authorities(self.exporter_contact)
        assert not can_user_edit_firearm_authorities(self.exporter_agent_contact)

    def test_can_user_edit_org(self):
        #
        # Test importer org access
        #
        assert can_user_edit_org(self.importer_contact, self.importer)
        assert can_user_edit_org(self.importer_contact, self.agent_importer)
        # Agents can't edit main orgs
        assert not can_user_edit_org(self.importer_agent_contact, self.importer)
        assert can_user_edit_org(self.importer_agent_contact, self.agent_importer)

        #
        # Test exporter org access
        #
        assert can_user_edit_org(self.exporter_contact, self.exporter)
        assert can_user_edit_org(self.exporter_contact, self.agent_exporter)
        # Agents can't edit main orgs
        assert not can_user_edit_org(self.exporter_agent_contact, self.exporter)
        assert can_user_edit_org(self.exporter_agent_contact, self.agent_exporter)

        #
        # Test ILB org access
        #
        assert can_user_edit_org(self.ilb_admin, self.importer)
        assert can_user_edit_org(self.ilb_admin, self.agent_importer)
        assert can_user_edit_org(self.ilb_admin, self.exporter)
        assert can_user_edit_org(self.ilb_admin, self.agent_exporter)

        #
        # Test no edit org access
        #
        assert not can_user_edit_org(self.importer_contact, self.exporter)
        assert not can_user_edit_org(self.importer_contact, self.agent_exporter)
        assert not can_user_edit_org(self.importer_agent_contact, self.exporter)
        assert not can_user_edit_org(self.importer_agent_contact, self.agent_exporter)

        assert not can_user_edit_org(self.exporter_contact, self.importer)
        assert not can_user_edit_org(self.exporter_contact, self.agent_importer)
        assert not can_user_edit_org(self.exporter_agent_contact, self.importer)
        assert not can_user_edit_org(self.exporter_agent_contact, self.agent_importer)

    def test_can_user_edit_section5_authorities(self):
        #
        # ILB admins have the "edit_firearm_authorities" permission
        #
        assert can_user_edit_section5_authorities(self.ilb_admin)

        #
        # Applicants do not
        #
        assert not can_user_edit_section5_authorities(self.importer_contact)
        assert not can_user_edit_section5_authorities(self.importer_agent_contact)
        assert not can_user_edit_section5_authorities(self.exporter_contact)
        assert not can_user_edit_section5_authorities(self.exporter_agent_contact)

    def test_can_user_manage_org_contacts(self):
        #
        # ILB admins can always manage contacts
        #
        assert can_user_manage_org_contacts(self.ilb_admin, self.importer)
        assert can_user_manage_org_contacts(self.ilb_admin, self.agent_importer)
        assert can_user_manage_org_contacts(self.ilb_admin, self.exporter)
        assert can_user_manage_org_contacts(self.ilb_admin, self.agent_exporter)

        #
        # Test importer / exporter permission
        #
        assert can_user_manage_org_contacts(self.importer_contact, self.importer)
        assert can_user_manage_org_contacts(self.importer_contact, self.agent_importer)
        assert not can_user_manage_org_contacts(self.importer_agent_contact, self.importer)
        assert not can_user_manage_org_contacts(self.importer_agent_contact, self.agent_importer)

        assert can_user_manage_org_contacts(self.exporter_contact, self.exporter)
        assert can_user_manage_org_contacts(self.exporter_contact, self.agent_exporter)
        assert not can_user_manage_org_contacts(self.exporter_agent_contact, self.exporter)
        assert not can_user_manage_org_contacts(self.exporter_agent_contact, self.agent_exporter)

    def test_constabulary_add_contact(self):
        constabulary = Constabulary.objects.get(name="Cumbria")

        # Check can add a user as a constabulary contact
        assert not self.importer_contact.groups.filter(
            name=Perms.obj.constabulary.get_group_name()
        ).exists()
        constabulary_add_contact(constabulary, self.importer_contact)
        assert self.importer_contact.groups.filter(
            name=Perms.obj.constabulary.get_group_name()
        ).exists()

    def test_constabulary_get_contacts(self, constabulary_contact):
        constabulary = Constabulary.objects.get(name="Derbyshire")

        contacts = constabulary_get_contacts(constabulary)
        assert contacts.count() == 1
        assert contacts[0] == constabulary_contact

        contacts = constabulary_get_contacts(
            constabulary, perms=[Perms.obj.constabulary.verified_fa_authority_editor.codename]
        )
        assert contacts.count() == 1
        assert contacts[0] == constabulary_contact

    def test_constabulary_remove_contact(self, constabulary_contact):
        constabulary = Constabulary.objects.get(name="Derbyshire")

        contacts = constabulary_get_contacts(constabulary)
        assert contacts.count() == 1
        assert contacts[0] == constabulary_contact

        constabulary_remove_contact(constabulary, constabulary_contact)

        contacts = constabulary_get_contacts(constabulary)
        assert contacts.count() == 0

        #
        # Test removing all other linked constabularies removes group.
        #
        assert constabulary_contact.groups.filter(
            name=Perms.obj.constabulary.get_group_name()
        ).exists()

        for con_name in ["Nottingham", "Lincolnshire"]:
            constabulary = Constabulary.objects.get(name=con_name)
            constabulary_remove_contact(constabulary, constabulary_contact)

        assert not constabulary_contact.groups.filter(
            name=Perms.obj.constabulary.get_group_name()
        ).exists()

    def test_can_user_view_org(self):
        assert can_user_view_org(self.ilb_admin, self.importer)
        assert can_user_view_org(self.importer_contact, self.importer)
        assert can_user_view_org(self.importer_contact, self.agent_importer)
        assert not can_user_view_org(self.importer_agent_contact, self.importer)
        assert not can_user_view_org(self.exporter_contact, self.importer)
        assert not can_user_view_org(self.exporter_agent_contact, self.importer)

        assert can_user_view_org(self.ilb_admin, self.exporter)
        assert can_user_view_org(self.exporter_contact, self.exporter)
        assert can_user_view_org(self.exporter_contact, self.agent_exporter)
        assert not can_user_view_org(self.exporter_agent_contact, self.exporter)
        assert not can_user_view_org(self.importer_contact, self.exporter)
        assert not can_user_view_org(self.importer_agent_contact, self.exporter)

    def test_can_user_view_search_cases(self):
        assert can_user_view_search_cases(self.importer_contact, "import")
        assert not can_user_view_search_cases(self.importer_contact, "export")

        assert can_user_view_search_cases(self.exporter_contact, "export")
        assert not can_user_view_search_cases(self.exporter_contact, "import")

        assert not can_user_view_search_cases(self.importer_contact, "invalid")

    def test_get_users_with_permission(self):
        importer_users = get_users_with_permission(Perms.sys.importer_access).values_list(
            "username", flat=True
        )
        assert list(importer_users) == [
            "I1_A1_main_contact",
            "I1_main_contact",
            "I2_main_contact",
            "individual_importer_user",
        ]

        exporter_users = get_users_with_permission(Perms.sys.exporter_access).values_list(
            "username", flat=True
        )
        assert list(exporter_users) == [
            "E1_A1_main_contact",
            "E1_main_contact",
            "E1_secondary_contact",
            "E2_main_contact",
            "prototype_export_agent_user",
            "prototype_export_user",
        ]

        ilb_admin_users = get_users_with_permission(Perms.sys.ilb_admin).values_list(
            "username", flat=True
        )
        assert list(ilb_admin_users) == ["ilb_admin_two", "ilb_admin_user", "san_admin_user"]

    def test_get_all_case_officers(self):
        case_officers = get_all_case_officers().values_list("username", flat=True)

        assert list(case_officers) == ["ilb_admin_two", "ilb_admin_user", "san_admin_user"]

    def test_get_ilb_case_officers(self):
        case_officers = get_ilb_case_officers().values_list("username", flat=True)

        assert list(case_officers) == ["ilb_admin_two", "ilb_admin_user"]

    def test_get_sanctions_case_officers(self):
        case_officers = get_sanctions_case_officers().values_list("username", flat=True)

        assert list(case_officers) == ["san_admin_user"]

    def test_get_org_obj_permissions(self):
        perms = get_org_obj_permissions(self.importer)
        assert perms.edit == Perms.obj.importer.edit
        assert perms.view == Perms.obj.importer.view
        assert perms.manage_contacts_and_agents == Perms.obj.importer.manage_contacts_and_agents

        perms = get_org_obj_permissions(self.exporter)
        assert perms.edit == Perms.obj.exporter.edit
        assert perms.view == Perms.obj.exporter.view
        assert perms.manage_contacts_and_agents == Perms.obj.exporter.manage_contacts_and_agents

        # Anything else raises an exception
        with pytest.raises(ValueError, match=r"Unknown org .+"):
            get_org_obj_permissions(object())

    def test_get_user_exporter_permissions(self):
        uop = get_user_exporter_permissions(self.exporter_contact)

        assert uop.count() == 1
        exp_uop = uop[0]

        assert exp_uop.user_id == self.exporter_contact.id
        assert exp_uop.content_object_id == self.exporter.id
        assert sorted(exp_uop.org_permissions) == sorted(
            [
                Perms.obj.exporter.manage_contacts_and_agents.codename,
                Perms.obj.exporter.edit.codename,
                Perms.obj.exporter.view.codename,
            ]
        )

        # Filtering by a single object is also supported
        uop = get_user_exporter_permissions(self.exporter_contact, self.exporter)
        exp_uop = uop[0]

        assert exp_uop.user_id == self.exporter_contact.id
        assert exp_uop.content_object_id == self.exporter.id
        assert sorted(exp_uop.org_permissions) == sorted(
            [
                Perms.obj.exporter.manage_contacts_and_agents.codename,
                Perms.obj.exporter.edit.codename,
                Perms.obj.exporter.view.codename,
            ]
        )

    def test_get_user_importer_permissions(self):
        uop = get_user_importer_permissions(self.importer_contact)

        assert uop.count() == 1
        imp_uop = uop[0]

        assert imp_uop.user_id == self.importer_contact.id
        assert imp_uop.content_object_id == self.importer.id
        assert sorted(imp_uop.org_permissions) == sorted(
            [
                Perms.obj.importer.manage_contacts_and_agents.codename,
                Perms.obj.importer.edit.codename,
                Perms.obj.importer.view.codename,
            ]
        )

        # Filtering by a single object is also supported
        uop = get_user_importer_permissions(self.importer_contact, self.importer)
        imp_uop = uop[0]

        assert imp_uop.user_id == self.importer_contact.id
        assert imp_uop.content_object_id == self.importer.id
        assert sorted(imp_uop.org_permissions) == sorted(
            [
                Perms.obj.importer.manage_contacts_and_agents.codename,
                Perms.obj.importer.edit.codename,
                Perms.obj.importer.view.codename,
            ]
        )

    def test_organisation_add_contact(self):
        #
        # Check can add an importer contact to an exporter
        #
        assert not self.exporter_contact.groups.filter(
            name=Perms.obj.importer.get_group_name()
        ).exists()
        organisation_add_contact(self.importer, self.exporter_contact)
        assert self.exporter_contact.groups.filter(
            name=Perms.obj.importer.get_group_name()
        ).exists()

        #
        # Check can add an exporter contact to an importer
        #
        assert not self.importer_contact.groups.filter(
            name=Perms.obj.exporter.get_group_name()
        ).exists()
        organisation_add_contact(self.exporter, self.importer_contact)
        assert self.importer_contact.groups.filter(
            name=Perms.obj.exporter.get_group_name()
        ).exists()

        #
        # Check can add to an agent importer
        #
        organisation_add_contact(self.agent_exporter, self.importer_contact)
        assert self.importer_contact.has_perm(Perms.obj.exporter.is_agent, self.exporter)

    def test_organisation_add_contact_assign_manage_permission(self):
        #
        # Check exporter contact has manage_contacts_and_agents for importer
        #
        organisation_add_contact(self.importer, self.exporter_contact, assign_manage=True)
        assert self.exporter_contact.has_perm(
            Perms.obj.importer.manage_contacts_and_agents, self.importer
        )

        #
        # Check importer contact has manage_contacts_and_agents for exporter
        #
        organisation_add_contact(self.exporter, self.importer_contact, assign_manage=True)
        assert self.importer_contact.has_perm(
            Perms.obj.exporter.manage_contacts_and_agents, self.exporter
        )

        #
        # Check assigning manage_contacts_and_agents permission for agent raises ValueError
        #
        with pytest.raises(
            ValueError, match="Unable to assign manage perm to agent org: Test Exporter 1 Agent 1"
        ):
            organisation_add_contact(self.agent_exporter, self.importer_contact, assign_manage=True)

    def test_organisation_get_contacts(self):
        importer_contacts = organisation_get_contacts(self.importer)
        for i in importer_contacts:
            print(i.username)
        assert importer_contacts.count() == 1

        remove_perm(Perms.obj.importer.edit, self.importer_contact, self.importer)
        importer_contacts = organisation_get_contacts(
            self.importer, perms=[Perms.obj.importer.edit.codename]
        )
        assert importer_contacts.count() == 0

        exporter_contacts = organisation_get_contacts(self.exporter)
        assert exporter_contacts.count() == 3

        exporter_contacts = organisation_get_contacts(
            self.exporter, perms=[Perms.obj.exporter.manage_contacts_and_agents.codename]
        )
        assert exporter_contacts.count() == 3

        remove_perm(
            Perms.obj.exporter.manage_contacts_and_agents, self.exporter_contact, self.exporter
        )

        exporter_contacts = organisation_get_contacts(
            self.exporter, perms=[Perms.obj.exporter.manage_contacts_and_agents.codename]
        )
        assert exporter_contacts.count() == 2

    def test_organisation_remove_contact(self):
        #
        # Check importer contact before and after
        #
        assert self.importer_contact.groups.filter(
            name=Perms.obj.importer.get_group_name()
        ).exists()
        organisation_remove_contact(self.importer, self.importer_contact)
        assert not self.importer_contact.groups.filter(
            name=Perms.obj.importer.get_group_name()
        ).exists()

        #
        # Check exporter contact before and after
        #
        assert self.exporter_contact.groups.filter(
            name=Perms.obj.exporter.get_group_name()
        ).exists()
        organisation_remove_contact(self.exporter, self.exporter_contact)
        assert not self.exporter_contact.groups.filter(
            name=Perms.obj.exporter.get_group_name()
        ).exists()

        #
        # Test removing an agent
        #
        organisation_add_contact(self.agent_exporter, self.exporter_contact)
        assert self.exporter_contact.has_perm(Perms.obj.exporter.is_agent, self.exporter)

        # Request new instance of User
        # Be aware that user.refresh_from_db() won't clear the cache.
        self.exporter_contact = User.objects.get(pk=self.exporter_contact.pk)

        self.exporter_contact.get_all_permissions()
        organisation_remove_contact(self.agent_exporter, self.exporter_contact)
        assert not self.exporter_contact.has_perm(Perms.obj.exporter.is_agent, self.exporter)

    def test_organisation_remove_contact_multiple_orgs(self, exporter_two):
        # Link a user with multiple exporters
        organisation_add_contact(exporter_two, self.exporter_contact)
        organisation_remove_contact(exporter_two, self.exporter_contact)

        # The user should still have exporter access as it's linked to exporter_one
        assert self.exporter_contact.groups.filter(
            name=Perms.obj.exporter.get_group_name()
        ).exists()

    @pytest.mark.parametrize(
        "report_type,expected_result",
        ((ReportType.ISSUED_CERTIFICATES, False), (ReportType.SUPPLEMENTARY_FIREARMS, True)),
    )
    def test_can_user_view_report(self, report_type, expected_result, nca_admin_user):
        report = Report.objects.get(report_type=report_type)
        assert can_user_view_report(nca_admin_user, report) == expected_result

    def test_all_reports_have_permission(self):
        # A test to confirm all report types have a unique page permission
        expected_permissions = {
            ReportType.ISSUED_CERTIFICATES: "web.can_view_report_issued_certificates",
            ReportType.ACCESS_REQUESTS: "web.can_view_report_access_requests",
            ReportType.IMPORT_LICENCES: "web.can_view_report_import_licences",
            ReportType.SUPPLEMENTARY_FIREARMS: "web.can_view_report_supplementary_firearms",
            ReportType.FIREARMS_LICENCES: "web.can_view_report_firearms_licences",
            ReportType.ACTIVE_USERS: "web.can_view_report_active_users",
        }
        for report_type, _ in ReportType.choices:
            report = Report.objects.get(report_type=report_type)
            assert get_report_permission(report) == expected_permissions[report.report_type]

    def test_get_report_permission_unknown(self):
        report = Report.objects.get(report_type=ReportType.IMPORT_LICENCES)
        report.report_type = "TEST"
        with pytest.raises(ValueError, match="Unknown Report Type TEST"):
            get_report_permission(report)

    @pytest.mark.parametrize(
        "perm,expected_report_type",
        (
            (Perms.sys.access_reports, None),
            (Perms.page.view_report_import_licences, ReportType.IMPORT_LICENCES),
            (Perms.page.view_report_supplementary_firearms, ReportType.SUPPLEMENTARY_FIREARMS),
            (Perms.page.view_report_access_requests, ReportType.ACCESS_REQUESTS),
            (Perms.page.view_report_firearms_licences, ReportType.FIREARMS_LICENCES),
            (Perms.page.view_report_issued_certificates, ReportType.ISSUED_CERTIFICATES),
        ),
    )
    def test_get_report_type_for_permission(self, perm, expected_report_type):
        assert get_report_type_for_permission(perm) == expected_report_type

    @pytest.mark.parametrize(
        "process_type,expected_email_addresses",
        [
            (
                ProcessTypes.SANCTIONS,
                [
                    "ilb_admin_two@example.com",  # /PS-IGNORE
                    "ilb_admin_user@example.com",  # /PS-IGNORE
                    "san_admin_user@example.com",  # /PS-IGNORE
                ],
            ),
            (
                ProcessTypes.FA_DFL,
                [
                    "ilb_admin_two@example.com",  # /PS-IGNORE
                    "ilb_admin_user@example.com",  # /PS-IGNORE
                ],
            ),
        ],
    )
    def test_get_case_officers_for_process_type(self, process_type, expected_email_addresses):
        assert [
            user.email for user in get_case_officers_for_process_type(process_type)
        ] == expected_email_addresses

    def test_is_user_agent_of_org(self):
        tests = [
            (self.importer, self.importer_contact, False),
            (self.importer, self.importer_agent_contact, True),
            (self.importer, self.exporter_contact, False),
            (self.importer, self.exporter_agent_contact, False),
            (self.agent_importer, self.importer_contact, False),
            (self.agent_importer, self.importer_agent_contact, False),
            (self.agent_importer, self.exporter_contact, False),
            (self.agent_importer, self.exporter_agent_contact, False),
            (self.exporter, self.importer_contact, False),
            (self.exporter, self.importer_agent_contact, False),
            (self.exporter, self.exporter_contact, False),
            (self.exporter, self.exporter_agent_contact, True),
            (self.agent_exporter, self.importer_contact, False),
            (self.agent_exporter, self.importer_agent_contact, False),
            (self.agent_exporter, self.exporter_contact, False),
            (self.agent_exporter, self.exporter_agent_contact, False),
        ]

        for org, user, is_agent in tests:
            assert is_user_agent_of_org(user, org) is is_agent


def test_filter_users_with_org_access():
    # Added for 100% test coverage
    users = User.objects.all()

    with pytest.raises(ValueError, match=r"Unknown org "):
        filter_users_with_org_access(object(), users)


def test__is_org_admin_raises(db):
    # Added for 100% test coverage
    with pytest.raises(ValueError, match=r"Unknown org "):
        is_user_org_admin(User.objects.first(), object())
