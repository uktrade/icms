import datetime as dt

from data_migration.queries import user

from . import xml_data as xd

user_query_result = {
    user.users: (
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
            ),
            (
                2,  # id
                "test_user",  # username
                "Test",  # first_name
                "User",  # last_name
                "test.user",  # email
                1,  # is_active
                "31323334",  # salt 1234
                "FB8C301A3EBDA623029E0AACC9D3B21B",  # encrypted_password /PS-IGNORE
                "Mr",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                "3",  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
            ),
            (
                3,  # id
                "test_user_two",  # username
                "Testtwo",  # first_name
                "Usertwo",  # last_name
                "test.usertwo",  # email
                1,  # is_active
                "35363738",  # salt 5678
                "9E764661E6C292D49006E4AF99FB1793",  # encrypted_password /PS-IGNORE
                "Ms",  # title
                "Org",  # Oranisation
                "Dept",  # Department
                "IT",  # job_title
                "ACTIVE",  # account_status
                "test_user(WUA_ID=3, WUAH_ID=4)",  # account_status_by
                dt.date.today(),  # account_status_date
                dt.datetime(2022, 11, 1, 12, 32),  # last_login_datetime
                "FULL",  # password_disposition
            ),
        ],
    ),
    user.importers: (
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
        ],
    ),
    user.importer_offices: (
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
        ],
    ),
    user.exporters: (
        [
            ("id",),
            ("is_active",),
            ("name",),
            ("registered_number",),
            ("main_importer_id",),
        ],
        [
            (1, 1, "Test Org", 123, 2, None),
            (2, 1, "Test Agent", 124, "GB123456789013", 2, 1),
            (3, 0, "Test Inactive", 125, "GB123456789014", 2, None),
        ],
    ),
    user.exporter_offices: (
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
    user.access_requests: (
        [
            ("iar_id",),
            ("process_type",),
            ("reference",),
            ("status",),
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
}
