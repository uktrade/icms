import datetime as dt

from data_migration import queries

from . import xml_data as xd

user_query_result = {
    queries.users: (
        [
            ("id",),
            ("username",),
            ("first_name",),
            ("last_name",),
            ("email",),
            ("is_active",),
            ("salt",),
            ("encrypted_password",),
            ("title",),
            ("organisation",),
            ("department",),
            ("job_title",),
            ("account_status",),
            ("account_status_by",),
            ("account_status_date",),
            ("last_login_datetime",),
            ("password_disposition",),
            ("personal_email_xml",),
            ("alternative_email_xml",),
            ("telephone_xml",),
            ("share_contact_details",),
        ],
        [
            (
                0,  # id
                "GUEST",  # username
                "Guest",  # first_name
                "User",  # last_name
                "",  # email
                0,  # is_active
                None,  # salt 1234
                None,  # encrypted_password /PS-IGNORE
                None,  # title
                None,  # Oranisation
                None,  # Department
                None,  # job_title
                "INACTIVE",  # account_status
                None,  # account_status_by
                None,  # account_status_date
                None,  # last_login_datetime
                "FULL",  # password_disposition
                None,  # personal_email_xml
                None,  # alternative_email_xml
                None,  # telephone_xml
                0,  # share_contact_details
            ),
            (
                2,  # id
                "ilb_case_officer@example.com",  # username /PS-IGNORE
                "ILB",  # first_name
                "Case-Officer",  # last_name
                "ilb_case_officer@example.com",  # email /PS-IGNORE
                1,  # is_active
                "31323334",  # salt 1234
                "FB8C301A3EBDA623029E0AACC9D3B21B",  # encrypted_password /PS-IGNORE
                "Mr",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                "2",  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                xd.personal_email_xml,  # personal_email_xml
                xd.alternative_email_xml,  # alternative_email_xml
                xd.phone_number_xml,  # telephone_xml
                1,  # share_contact_details
            ),
            (
                3,  # id
                "home_office@example.com",  # username /PS-IGNORE
                "Home",  # first_name
                "Office",  # last_name
                "home_office@example.com",  # email  /PS-IGNORE
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                3,  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                None,  # personal_email_xml
                None,  # alternative_email_xml
                None,  # telephone_xml
                0,  # share_contact_details
            ),
            (
                4,  # id
                "nca@example.com",  # username /PS-IGNORE
                "NCA",  # first_name
                "User",  # last_name
                "nca@example.com",  # email  /PS-IGNORE
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                4,  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                None,  # personal_email_xml
                None,  # alternative_email_xml
                None,  # telephone_xml
                0,  # share_contact_details
            ),
            (
                5,  # id
                "importer_editor@example.com",  # username /PS-IGNORE
                "Importer",  # first_name
                "Editor",  # last_name
                "importer_editor@example.com",  # email  /PS-IGNORE
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                5,  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                None,  # personal_email_xml
                None,  # alternative_email_xml
                None,  # telephone_xml
                0,  # share_contact_details
            ),
            (
                6,  # id
                "importer_viewer@example.com",  # username /PS-IGNORE
                "Importer",  # first_name
                "Viewer",  # last_name
                "importer_viwer@example.com",  # email  /PS-IGNORE
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                6,  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                None,  # personal_email_xml
                None,  # alternative_email_xml
                None,  # telephone_xml
                0,  # share_contact_details
            ),
            (
                7,  # id
                "importer_agent_editor@example.com",  # username /PS-IGNORE
                "Importer Agent",  # first_name
                "Editor",  # last_name
                "importer_agent_editor@example.com",  # email  /PS-IGNORE
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                7,  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                None,  # personal_email_xml
                None,  # alternative_email_xml
                None,  # telephone_xml
                0,  # share_contact_details
            ),
            (
                8,  # id
                "importer_agent_viewer@example.com",  # username /PS-IGNORE
                "Importer Agent",  # first_name
                "Viewer",  # last_name
                "importer_agent_viwer@example.com",  # email  /PS-IGNORE
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                8,  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                None,  # personal_email_xml
                None,  # alternative_email_xml
                None,  # telephone_xml
                0,  # share_contact_details
            ),
            (
                9,  # id
                "exporter_editor@example.com",  # username /PS-IGNORE
                "Exporter",  # first_name
                "Editor",  # last_name
                "Exporter_editor@example.com",  # email  /PS-IGNORE
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                9,  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                None,  # personal_email_xml
                None,  # alternative_email_xml
                None,  # telephone_xml
                0,  # share_contact_details
            ),
            (
                10,  # id
                "exporter_viewer@example.com",  # username /PS-IGNORE
                "Exporter",  # first_name
                "Viewer",  # last_name
                "exporter_viwer@example.com",  # email  /PS-IGNORE
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                10,  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                None,  # personal_email_xml
                None,  # alternative_email_xml
                None,  # telephone_xml
                0,  # share_contact_details
            ),
            (
                11,  # id
                "exporter_agent_editor@example.com",  # username /PS-IGNORE
                "Exporter Agent",  # first_name
                "Editor",  # last_name
                "exporter_agent_editor@example.com",  # email  /PS-IGNORE
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                11,  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                None,  # personal_email_xml
                None,  # alternative_email_xml
                None,  # telephone_xml
                0,  # share_contact_details
            ),
            (
                12,  # id
                "exporter_agent_viewer@example.com",  # username /PS-IGNORE
                "Exporter Agent",  # first_name
                "Viewer",  # last_name
                "exporter_agent_viwer@example.com",  # email  /PS-IGNORE
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                12,  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                None,  # personal_email_xml
                None,  # alternative_email_xml
                None,  # telephone_xml
                0,  # share_contact_details
            ),
            (
                13,  # id
                "constabulary_contact@example.com",  # username /PS-IGNORE
                "Constabulary",  # first_name
                "Contact",  # last_name
                "constabulary_contact@example.com",  # email  /PS-IGNORE
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                13,  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                None,  # personal_email_xml
                None,  # alternative_email_xml
                None,  # telephone_xml
                0,  # share_contact_details
            ),
            (
                14,  # id
                "import_search_user@example.com",  # username /PS-IGNORE
                "Import",  # first_name
                "Search",  # last_name
                "import_search_user@example.com",  # email  /PS-IGNORE
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                14,  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                None,  # personal_email_xml
                None,  # alternative_email_xml
                None,  # telephone_xml
                0,  # share_contact_details
            ),
            (
                15,  # id
                "test@example.org",  # username /PS-IGNORE
                "Test",  # first_name
                "User",  # last_name
                "test@example.org",  # email  /PS-IGNORE
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                14,  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
                xd.personal_email_excluded_xml,  # personal_email_xml
                None,  # alternative_email_xml
                xd.phone_number_excluded_xml,  # telephone_xml
                0,  # share_contact_details
            ),
        ],
    ),
    queries.importers: (
        [
            ("id",),
            ("is_active",),
            ("type",),
            ("name",),
            ("registered_number",),
            ("eori_number",),
            ("user_id",),
            ("main_importer_id",),
            ("region_origin",),
        ],
        [
            (1, 1, "INDIVIDUAL", None, 123, "GB123456789012", 2, None, "O"),
            (2, 1, "ORGANISATION", "Test Org", 124, "GB123456789013", 2, None, None),
            (3, 1, "INDIVIDUAL", "Test Agent", 125, "GB123456789014", 2, 2, None),
            (4, 1, "INDIVIDUAL", "Test Excluded", 126, "GB123456789015", 15, 2, None),
        ],
    ),
    queries.importer_offices: (
        [
            ("importer_id",),
            ("legacy_id",),
            ("is_active",),
            ("postcode",),
            ("address",),
            ("eori_number",),
            ("address_entry_type",),
        ],
        [
            (2, "i-2-1", 1, "ABC", "123 Test\nTest City", "GB123456789015", "SEARCH"),
            (2, "i-2-2", 1, "DEF", "456 Test", "GB123456789016", "MANUAL"),
            (
                3,
                "i-3-1",
                1,
                "deletethisTESTLONG",
                "ABC Test\nTest Town\nTest City",
                "GB123456789017",
                "MANUAL",
            ),
            (4, "i-4-1", 1, "EXC", "123 Excluded", "GB123456789017", "MANUAL"),
        ],
    ),
    queries.exporters: (
        [
            ("id",),
            ("is_active",),
            ("name",),
            ("registered_number",),
            ("main_exporter_id",),
        ],
        [
            (1, 1, "Test Org", 123, None),
            (2, 1, "Test Agent", 124, 1),
            (3, 0, "Test Inactive", 125, None),
        ],
    ),
    queries.exporter_offices: (
        [
            ("exporter_id",),
            ("legacy_id",),
            ("is_active",),
            ("postcode",),
            ("address",),
            ("address_entry_type",),
        ],
        [
            (2, "e-2-1", 1, "Exp A", "123 Test\nTest City", "SEARCH"),
            (2, "e-2-2", 1, "Very Long Postcode", "456 Test", "MANUAL"),
            (
                3,
                "e-3-1",
                0,
                "TEST",
                "ABC Test\nTest Town\nTest City",
                "MANUAL",
            ),
        ],
    ),
    queries.access_requests: (
        [
            ("iar_id",),
            ("process_type",),
            ("reference",),
            ("status",),
            ("created",),
            ("request_type",),
            ("submit_datetime",),
            ("submitted_by_id",),
            ("last_update_datetime",),
            ("last_updated_by_id",),
            ("closed_datetime",),
            ("closed_by_id",),
            ("organisation_name",),
            ("organisation_address",),
            ("request_reason",),
            ("agent_name",),
            ("agent_address",),
            ("response",),
            ("response_reason",),
            ("importer_id",),
            ("exporter_id",),
            ("fir_xml",),
            ("approval_xml",),
        ],
        [
            (
                1,  # iar_id
                "ImporterAccessRequest",  # process_type
                "IAR/0001",  # reference
                "SUBMITTED",  # status
                dt.datetime(2022, 11, 14, 8, 24),  # created
                "MAIN_IMPORTER_ACCESS",  # request_type
                dt.datetime(2022, 11, 14),  # submit_datetime
                2,  # submitted_by_id
                dt.datetime(2022, 11, 14),  # last_updated_datetime
                2,  # last_updated_by_id
                None,  # closed_datetime
                None,  # closed_by_id
                "Test Org",  # organisation_name
                "Test Address",  # organisation_address
                "Test Reason",  # request_reason
                None,  # agent_name
                None,  # agent_address
                None,  # response
                None,  # response_reason
                2,  # importer_id
                None,  # exporter_id
                None,  # fir_xml
                None,  # approval_xml
            ),
            (
                2,  # iar_id
                "ImporterAccessRequest",  # process_type
                "IAR/0002",  # reference
                "CLOSED",  # status
                dt.datetime(2022, 11, 14, 8, 47),  # created
                "AGENT_IMPORTER_ACCESS",  # request_type
                dt.datetime(2022, 11, 14),  # submit_datetime
                2,  # submitted_by_id
                dt.datetime(2022, 11, 14),  # last_updated_datetime
                2,  # last_updated_by_id
                dt.datetime(2022, 11, 14),  # closed_datetime
                2,  # closed_by_id
                "Test Org",  # organisation_name
                "Test Address",  # organisation_address
                "Test Reason",  # request_reason
                "Test Name",  # agent_name
                "Test Address",  # agent_address
                "APPROVED",  # response
                "Test Reason",  # response_reason
                3,  # importer_id
                None,  # exporter_id
                None,  # fir_xml
                xd.import_approval_request_xml,  # approval_xml
            ),
            (
                3,  # iar_id
                "ExporterAccessRequest",  # process_type
                "EAR/0003",  # reference
                "CLOSED",  # status
                dt.datetime(2022, 11, 14, 10, 52),  # created
                "MAIN_EXPORTER_ACCESS",  # request_type
                dt.datetime(2022, 11, 14),  # submit_datetime
                2,  # submitted_by_id
                dt.datetime(2022, 11, 14),  # last_updated_datetime
                2,  # last_updated_by_id
                dt.datetime(2022, 11, 14),  # closed_datetime
                2,  # closed_by_id
                "Test Org",  # organisation_name
                "Test Address",  # organisation_address
                "Test Reason",  # request_reason
                None,  # agent_name
                None,  # agent_address
                "APPROVED",  # response
                "Test Reason",  # response_reason
                None,  # importer_id
                2,  # exporter_id
                xd.export_fir_xml_2,  # fir_xml
                None,  # approval_xml
            ),
            (
                4,  # iar_id
                "ExporterAccessRequest",  # process_type
                "EAR/0004",  # reference
                "CLOSED",  # status
                dt.datetime(2022, 11, 14, 10, 52),  # created
                "AGENT_EXPORTER_ACCESS",  # request_type
                dt.datetime(2022, 11, 14),  # submit_datetime
                2,  # submitted_by_id
                dt.datetime(2022, 11, 14),  # last_updated_datetime
                2,  # last_updated_by_id
                dt.datetime(2022, 11, 14),  # closed_datetime
                2,  # closed_by_id
                "Test Org",  # organisation_name
                "Test Address",  # organisation_address
                "Test Reason",  # request_reason
                "Test Agent",  # agent_name
                "Test Address",  # agent_address
                "APPROVED",  # response
                "Test Reason",  # response_reason
                None,  # importer_id
                3,  # exporter_id
                None,  # fir_xml
                xd.export_approval_request_xml,  # approval_xml
            ),
        ],
    ),
    queries.ilb_user_roles: (
        [("username",), ("roles",)],
        [
            (
                "ilb_case_officer@example.com",  # /PS-IGNORE
                "IMP_CASE_OFFICERS:CASE_OFFICER, IMP_CASE_OFFICERS:CA_CASE_OFFICER",
            )
        ],
    ),
    queries.nca_user_roles: (
        [("username",), ("roles",)],
        [
            (
                "nca@example.com",  # /PS-IGNORE
                "IMP_ADMIN:DASHBOARD_USER, REPORTING_TEAM:REPORT_RUNNER_NOW, REPORTING_TEAM:REPORT_VIEWER",
            )
        ],
    ),
    queries.home_office_user_roles: (
        [("username",), ("roles",)],
        [
            (
                "home_office@example.com",  # /PS-IGNORE
                "IMP_EXTERNAL:SECTION5_AUTHORITY_EDITOR, IMP_ADMIN_SEARCH:SEARCH_CASES",
            )
        ],
    ),
    queries.import_search_user_roles: (
        [("username",), ("roles",)],
        [
            (
                "import_search_user@example.com",  # /PS-IGNORE
                "IMP_ADMIN_SEARCH:SEARCH_CASES",
            )
        ],
    ),
    queries.constabulary_user_roles: (
        [("username",), ("roles",), ("constabulary_id",)],
        [
            (
                "constabulary_contact@example.com",  # /PS-IGNORE
                "IMP_CONSTABULARY_CONTACTS:FIREARMS_AUTHORITY_EDITOR",
                1,
            )
        ],
    ),
    queries.importer_user_roles: (
        [
            ("username",),
            ("roles"),
            ("importer_id",),
        ],
        [
            (
                "importer_viewer@example.com",  # /PS-IGNORE
                "IMP_IMPORTER_CONTACTS:VIEW_APP",
                2,
            ),
            (
                "importer_editor@example.com",  # /PS-IGNORE
                "IMP_IMPORTER_CONTACTS:AGENT_APPROVER, IMP_IMPORTER_CONTACTS:EDIT_APP",
                2,
            ),
            (
                "importer_agent_viewer@example.com",  # /PS-IGNORE
                "IMP_IMPORTER_AGENT_CONTACTS:VIEW_APP",
                3,
            ),
            (
                "importer_agent_editor@example.com",  # /PS-IGNORE
                "IMP_IMPORTER_AGENT_CONTACTS:VIEW_APP, IMP_IMPORTER_AGENT_CONTACTS:VARY_APP",
                3,
            ),
        ],
    ),
    queries.exporter_user_roles: (
        [
            ("username",),
            ("roles",),
            ("exporter_id",),
        ],
        [
            (
                "exporter_viewer@example.com",  # /PS-IGNORE
                "IMP_EXPORTER_CONTACTS:VIEW_APP",
                1,
            ),
            (
                "exporter_editor@example.com",  # /PS-IGNORE
                "IMP_EXPORTER_CONTACTS:AGENT_APPROVER, IMP_EXPORTER_CONTACTS:EDIT_APP",
                1,
            ),
            (
                "exporter_agent_viewer@example.com",  # /PS-IGNORE
                "IMP_EXPORTER_AGENT_CONTACTS:VIEW_APP",
                2,
            ),
            (
                "exporter_agent_editor@example.com",  # /PS-IGNORE
                "IMP_EXPORTER_AGENT_CONTACTS:VIEW_APP, IMP_EXPORTER_AGENT_CONTACTS:VARY_APP",
                2,
            ),
        ],
    ),
}
