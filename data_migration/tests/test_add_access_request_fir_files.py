import datetime as dt
from unittest import mock

import freezegun
import pytest

from data_migration import models as dm
from data_migration.management.commands import add_access_request_fir_files
from data_migration.management.commands.utils.db_processor import OracleDBProcessor
from data_migration.utils.format import datetime_or_none
from web.models import FurtherInformationRequest, ImporterAccessRequest

CREATED_DATETIME = dt.datetime.strptime("2024-01-01T01:00:00", "%Y-%m-%dT%H:%M:%S")


FAKE_DB_RESPONSE = {
    "BLOB_DATA": "blob",
    "PATH": "testfile.txt",
    "CREATED_DATETIME": CREATED_DATETIME,
    "SECURE_LOB_REF_ID": 1,
    "FILE_SIZE": 6 * 1024**2,
}

FAKE_FILE_DATA = {
    "FILENAME": "file.1.PDF",
    "FILE_SIZE": "181620",
    "CONTENT_TYPE": None,
    "CREATED_BY_ID": 0,
    "CREATED_DATETIME": CREATED_DATETIME,
    "PATH": "access_request_docs/file.1.pdf",
    "REQUEST_REFERENCE": "IAR/1002",
    "RFI_ID": "1000",
    "SECONDARY_DATA_UREF": "1IARRFI",
    "SECURE_LOB_REF_ID": 1,
    "FIR_REQUEST_SUBJECT": "files test subject",
    "ACCESS_REQUEST_ID": 1002,
    "FIR_REQUESTED_DATETIME": CREATED_DATETIME,
    "FIR_RESPONDED_DATETIME": CREATED_DATETIME,
}


@pytest.fixture
def setup_db_access_request():
    iar = ImporterAccessRequest.objects.create(
        process_type=ImporterAccessRequest.PROCESS_TYPE,
        request_type=ImporterAccessRequest.AGENT_ACCESS,
        status=ImporterAccessRequest.Statuses.CLOSED,
        response=ImporterAccessRequest.REFUSED,
        submitted_by_id=0,
        last_updated_by_id=0,
        reference="IAR/1002",
        organisation_name="Import Ltd",
        organisation_address="1 Main Street",
        agent_name="Test Agent",
        agent_address="1 Agent House",
        response_reason="Test refusing request",
    )
    with freezegun.freeze_time(CREATED_DATETIME):
        iar.further_information_requests.create(
            status=FurtherInformationRequest.DRAFT,
            requested_by_id=0,
            request_subject="files test subject",
            request_detail="body",
            process_type=FurtherInformationRequest.PROCESS_TYPE,
            response_datetime=datetime_or_none("2024-01-01T01:00:00"),
        )
        dm_user = dm.User.objects.create(username="test_user")
        process = dm.Process.objects.create(
            iar_id=1002,
            process_type=ImporterAccessRequest.PROCESS_TYPE,
            created=iar.submit_datetime,
        )
        dm.AccessRequest.objects.create(
            pk=iar.pk,
            iar=process,
            reference=iar.reference,
            submit_datetime=iar.submit_datetime,
            last_update_datetime=iar.last_update_datetime,
            submitted_by_id=dm_user.id,
            last_updated_by_id=dm_user.id,
        )


class TestAddAccessRequestFirFiles:
    @pytest.fixture(autouse=True)
    def setUp(self) -> None:
        self.cmd = self.get_cmd_to_test()

    def get_cmd_to_test(self):
        cmd = add_access_request_fir_files.Command()
        cmd.dry_run = False
        return cmd

    @mock.patch(
        "data_migration.management.commands.add_access_request_fir_files.Command.upload_file_to_s3"
    )
    @mock.patch(
        "data_migration.management.commands.add_access_request_fir_files.Command.add_file_to_db"
    )
    @mock.patch.object(OracleDBProcessor, "execute_query")
    @mock.patch.object(OracleDBProcessor, "execute_cumulative_query")
    def test_add_files_access_request_firs(
        self,
        mock_execute_count_query,
        mock_execute_query,
        mock_add_files_to_db,
        mock_upload_file_to_s3,
    ):
        mock_upload_file_to_s3.return_value = None
        mock_add_files_to_db.return_value = None
        mock_execute_count_query.return_value = 10, 1000
        mock_execute_query.return_value.__enter__.return_value = iter(
            [FAKE_DB_RESPONSE, FAKE_DB_RESPONSE]
        )
        self.cmd.add_files_access_request_firs(100, 0)
        assert mock_upload_file_to_s3.call_count == 2
        assert mock_add_files_to_db.call_count == 2

    @mock.patch(
        "data_migration.management.commands.add_access_request_fir_files.s3_web.upload_file_obj_to_s3"
    )
    @mock.patch(
        "data_migration.management.commands.add_access_request_fir_files.s3_web.upload_file_obj_to_s3_in_parts"
    )
    def test_upload_file_to_s3_in_parts(self, mock_upload_file_in_parts, mock_upload_file_obj):
        mock_upload_file_in_parts.return_value = None
        mock_upload_file_in_parts.return_value = None
        self.cmd.upload_file_to_s3(FAKE_DB_RESPONSE)
        assert mock_upload_file_in_parts.call_count == 1
        assert mock_upload_file_obj.call_count == 0

    @mock.patch(
        "data_migration.management.commands.add_access_request_fir_files.s3_web.upload_file_obj_to_s3"
    )
    @mock.patch(
        "data_migration.management.commands.add_access_request_fir_files.s3_web.upload_file_obj_to_s3_in_parts"
    )
    @pytest.mark.parametrize(
        "dry_run,expected_file_count",
        (
            (False, 1),
            (True, 0),
        ),
    )
    def test_upload_file_to_s3(
        self, mock_upload_file_in_parts, mock_upload_file_obj, dry_run, expected_file_count
    ):
        mock_upload_file_in_parts.return_value = None
        mock_upload_file_in_parts.return_value = None
        FAKE_DB_RESPONSE["FILE_SIZE"] = 1000
        self.cmd.dry_run = dry_run
        self.cmd.upload_file_to_s3(FAKE_DB_RESPONSE)
        assert mock_upload_file_in_parts.call_count == 0
        assert mock_upload_file_obj.call_count == expected_file_count

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "dry_run,expected_file_count",
        (
            (False, 1),
            (True, 0),
        ),
    )
    def test_add_file_to_db(self, setup_db_access_request, dry_run, expected_file_count):
        fir = FurtherInformationRequest.objects.get(request_subject="files test subject")
        assert fir.files.count() == 0
        self.cmd.dry_run = dry_run
        self.cmd.add_file_to_db(FAKE_FILE_DATA)
        fir.refresh_from_db()
        assert fir.files.count() == expected_file_count
