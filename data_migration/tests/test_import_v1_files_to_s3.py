import io
import json
from datetime import datetime
from unittest import mock

import freezegun
import pytest
from botocore.exceptions import ClientError

from data_migration.management.commands import import_v1_files_to_s3
from data_migration.management.commands._types import QueryModel
from data_migration.management.commands.config.run_order.files import (
    DEFAULT_FILE_CREATED_DATETIME,
    DEFAULT_SECURE_LOB_REF_ID,
)
from data_migration.management.commands.utils.db_processor import OracleDBProcessor

CREATED_DATETIME_ALT = "2023-01-01 01:00:00"
CREATED_DATETIME_ALT_2 = "2023-01-02 01:00:00"

FAKE_DB_RESPONSE = [
    {
        "BLOB_DATA": "blob",
        "PATH": "testfile.txt",
        "CREATED_DATETIME": datetime.strptime(CREATED_DATETIME_ALT, "%Y-%m-%d %H:%M:%S"),
        "SECURE_LOB_REF_ID": 1,
    },
    {
        "BLOB_DATA": "blob2",
        "PATH": "testfile2.txt",
        "CREATED_DATETIME": datetime.strptime(CREATED_DATETIME_ALT, "%Y-%m-%d %H:%M:%S"),
        "SECURE_LOB_REF_ID": 2,
    },
    {
        "BLOB_DATA": "blob2",
        "PATH": "testfile3.txt",
        "CREATED_DATETIME": datetime.strptime(CREATED_DATETIME_ALT_2, "%Y-%m-%d %H:%M:%S"),
        "SECURE_LOB_REF_ID": 3,
    },
]


class TestImportV1FilesToS3:
    @pytest.fixture(autouse=True)
    def setUp(self) -> None:
        self.test_query = QueryModel(
            "select * from test_query_table where col=:col_type",
            "test_query",
            None,
            {"secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID, "col_type": "col1"},
        )
        self.cmd = self.get_cmd_to_test()
        self.cmd.db.QUERIES = [self.test_query]

    def get_cmd_to_test(self):
        cmd = import_v1_files_to_s3.Command()
        cmd.db = OracleDBProcessor(100, ["test_query"], 1)
        cmd.run_data_batchsize = 100
        return cmd

    def test_get_query_last_run_key(self):
        assert import_v1_files_to_s3.get_query_last_run_key("TEST") == "TEST-last-run.json"

    def test_get_start_position_ignore_true(self):
        result = self.cmd.get_query_parameters(self.test_query, True)
        assert result == {"secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID, "col_type": "col1"}

    @mock.patch(
        "data_migration.management.commands.import_v1_files_to_s3.Command.get_last_run_data"
    )
    def test_get_start_position_ignore_false(self, mock_get_last_run_file):
        mock_get_last_run_file.return_value = {
            "created_datetime": "2024-01-01 12:00:00",
            "col_type": "col1",
            "secure_lob_ref_id": 123,
        }
        result = self.cmd.get_query_parameters(self.test_query, False)
        assert result == {
            "col_type": "col1",
            "secure_lob_ref_id": 123,
        }

    @mock.patch("web.utils.s3.get_s3_client")
    def test_get_last_run_data(self, mock_get_client):
        mock_get_client.return_value = FakeS3Client(b'{"created_datetime" : "hello"}')
        result = self.cmd.get_last_run_data(self.test_query)
        assert result == {"created_datetime": "hello"}

    @mock.patch("web.utils.s3.get_s3_client")
    def test_get_last_run_data_when_file_does_not_exist(self, mock_get_client):
        mock_get_client.return_value = FakeS3Client(None, raise_exception=True)
        result = self.cmd.get_last_run_data(self.test_query)
        assert result == {}

    @freezegun.freeze_time(CREATED_DATETIME_ALT)
    @mock.patch("data_migration.management.commands.import_v1_files_to_s3.s3_web.put_object_in_s3")
    @mock.patch(
        "data_migration.management.commands.import_v1_files_to_s3.s3_web.upload_file_obj_to_s3"
    )
    @mock.patch.object(OracleDBProcessor, "execute_query")
    def test_process_query_and_upload(
        self, mock_execute_query, mock_upload_file, mock_upload_last_run
    ):
        mock_upload_last_run.return_value = None

        mock_upload_file.return_value = None
        mock_execute_query.return_value.__enter__.return_value = iter(FAKE_DB_RESPONSE)

        self.cmd.process_query_and_upload(
            self.cmd.db.QUERIES[0],
            {"created_datetime": DEFAULT_FILE_CREATED_DATETIME},
            len(FAKE_DB_RESPONSE),
        )
        mock_upload_last_run(
            {
                "created_datetime": "2023-01-01 01:00:00",
                "finished_at": "2023-01-01 01:00:00",
                "number_of_files_processed": len(FAKE_DB_RESPONSE),
                "number_of_files_to_be_processed": len(FAKE_DB_RESPONSE),
                "query_name": "test_query",
                "started_at": "2023-01-01 01:00:00",
            }
        )

    @freezegun.freeze_time(CREATED_DATETIME_ALT)
    @mock.patch("data_migration.management.commands.import_v1_files_to_s3.s3_web.put_object_in_s3")
    @mock.patch(
        "data_migration.management.commands.import_v1_files_to_s3.s3_web.upload_file_obj_to_s3"
    )
    @mock.patch.object(OracleDBProcessor, "execute_query")
    def test_process_query_and_upload_no_data(
        self, mock_execute_query, mock_upload_file, mock_upload_last_run
    ):
        fake_db_rows = []
        mock_upload_file.return_value = None
        mock_upload_last_run.return_value = None
        mock_execute_query.return_value.__enter__.return_value = iter(fake_db_rows)
        self.cmd.process_query_and_upload(
            self.cmd.db.QUERIES[0],
            {"created_datetime": DEFAULT_FILE_CREATED_DATETIME},
            len(fake_db_rows),
        )
        assert mock_upload_last_run.called is False
        assert mock_upload_file.called is False

    @freezegun.freeze_time(CREATED_DATETIME_ALT)
    @mock.patch("data_migration.management.commands.import_v1_files_to_s3.s3_web.put_object_in_s3")
    @mock.patch(
        "data_migration.management.commands.import_v1_files_to_s3.s3_web.upload_file_obj_to_s3"
    )
    @mock.patch("data_migration.management.commands.import_v1_files_to_s3.s3_web.get_file_from_s3")
    @mock.patch.object(OracleDBProcessor, "execute_query")
    @mock.patch.object(OracleDBProcessor, "execute_count_query")
    def test_process_queries(
        self,
        mock_execute_count_query,
        mock_execute_query,
        mock_get_file_from_s3,
        mock_upload_file,
        mock_put_object_in_s3,
    ):
        mock_get_file_from_s3.return_value = (
            b'{"created_datetime": "2023-05-02 12:00:00", "secure_lob_ref_id": 0}'
        )
        mock_put_object_in_s3.return_value = None
        mock_upload_file.return_value = None
        mock_execute_count_query.return_value = 3, 1000
        mock_execute_query.return_value.__enter__.return_value = iter(FAKE_DB_RESPONSE)

        self.cmd.process_queries(False, False)

        assert mock_execute_count_query.called is True
        assert mock_execute_query.called is True
        assert mock_upload_file.call_count == 3
        assert mock_get_file_from_s3.called is True

        assert mock_put_object_in_s3.called is True
        mock_put_object_in_s3.assert_called_with(
            json.dumps(
                {
                    "number_of_files_to_be_processed": 3,
                    "number_of_files_processed": 3,
                    "query_name": "test_query",
                    "started_at": "2023-01-01 01:00:00",
                    "secure_lob_ref_id": 3,
                    "col_type": "col1",
                    "created_datetime": "2023-01-02 01:00:00",
                    "finished_at": "2023-01-01 01:00:00",
                }
            ),
            "test_query-last-run.json",
        )

    @freezegun.freeze_time(CREATED_DATETIME_ALT)
    @mock.patch("data_migration.management.commands.import_v1_files_to_s3.s3_web.put_object_in_s3")
    @mock.patch("data_migration.management.commands.import_v1_files_to_s3.s3_web.get_file_from_s3")
    @mock.patch.object(OracleDBProcessor, "execute_query")
    @mock.patch.object(OracleDBProcessor, "execute_count_query")
    def test_process_queries_count_only(
        self,
        mock_execute_count_query,
        mock_execute_query,
        mock_get_file_from_s3,
        mock_put_object_in_s3,
    ):
        mock_get_file_from_s3.return_value = None
        mock_put_object_in_s3.return_value = None
        mock_execute_count_query.return_value = 10, 1000
        mock_execute_query.return_value.__enter__.return_value = iter([])

        self.cmd.process_queries(True, True)

        assert mock_get_file_from_s3.called is False
        assert mock_execute_count_query.called is True
        assert mock_execute_query.called is False
        assert mock_put_object_in_s3.called is False

    @freezegun.freeze_time(CREATED_DATETIME_ALT)
    def test_get_initial_run_data_dict(self):
        parameters = {"created_datetime": "2023-05-02 12:00:00"}
        result = self.cmd.get_initial_run_data_dict(self.test_query, parameters, 123)
        assert result == {
            "number_of_files_processed": 0,
            "number_of_files_to_be_processed": 123,
            "query_name": "test_query",
            "started_at": "2023-01-01 01:00:00",
            "created_datetime": "2023-05-02 12:00:00",
        }

    @pytest.mark.parametrize(
        "number_of_files_processed,number_of_files_to_be_processed,expected_result",
        [
            (0, 100, False),
            (10, 10, True),
            (5, 10, True),
            (6, 10, False),
            (15, 16, True),
        ],
    )
    def test_should_save_run_data(
        self, number_of_files_processed, number_of_files_to_be_processed, expected_result
    ):
        self.cmd.run_data_batchsize = 5
        assert (
            self.cmd.should_save_run_data(
                number_of_files_processed, number_of_files_to_be_processed
            )
            == expected_result
        )

    @freezegun.freeze_time(CREATED_DATETIME_ALT)
    @mock.patch("data_migration.management.commands.import_v1_files_to_s3.s3_web.put_object_in_s3")
    def test_save_run_data(self, mock_put_object_in_s3):
        mock_put_object_in_s3.return_value = None
        self.cmd.save_run_data(
            {"query_name": "test_query", "number_of_files_to_be_processed": 2},
            2,
            FAKE_DB_RESPONSE[0],
        )
        assert mock_put_object_in_s3.called is True
        mock_put_object_in_s3.assert_called_with(
            json.dumps(
                {
                    "query_name": "test_query",
                    "number_of_files_to_be_processed": 2,
                    "number_of_files_processed": 2,
                    "created_datetime": "2023-01-01 01:00:00",
                    "finished_at": "2023-01-01 01:00:00",
                    "secure_lob_ref_id": 1,
                }
            ),
            "test_query-last-run.json",
        )

    @freezegun.freeze_time(CREATED_DATETIME_ALT)
    @mock.patch("data_migration.management.commands.import_v1_files_to_s3.s3_web.put_object_in_s3")
    def test_save_run_data_not_called(self, mock_put_object_in_s3):
        mock_put_object_in_s3.return_value = None
        self.cmd.save_run_data(
            {"query_name": "test_query", "number_of_files_to_be_processed": 3},
            2,
            FAKE_DB_RESPONSE[0],
        )
        assert mock_put_object_in_s3.called is False


class FakeS3Client:
    def __init__(self, response, raise_exception=False):
        self.response = response
        self.raise_exception = raise_exception

    def get_object(self, **kwargs):
        if self.raise_exception:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "get_object")
        return {"Body": self.wrap_response(self.response)}

    def wrap_response(self, data):
        _file = io.BytesIO()
        _file.write(data)
        _file.seek(0)
        return _file
