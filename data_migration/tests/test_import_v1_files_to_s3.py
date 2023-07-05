import io
import json
from datetime import datetime
from unittest import mock

import freezegun
from botocore.exceptions import ClientError
from django.test import TestCase

from data_migration.management.commands import import_v1_files_to_s3
from data_migration.management.commands._types import QueryModel
from data_migration.management.commands.config.run_order import (
    DEFAULT_FILE_CREATED_DATETIME,
)
from data_migration.management.commands.utils.db_processor import OracleDBProcessor

CREATED_DATETIME_ALT = "2023-01-01 01:00:00"


class TestImportV1FilesToS3(TestCase):
    def setUp(self) -> None:
        self.test_query = QueryModel(
            "select * from test_query_table",
            "test_query",
            None,
            {"created_datetime": DEFAULT_FILE_CREATED_DATETIME},
        )
        self.cmd = self.get_cmd_to_test()
        self.cmd.db.QUERIES = [self.test_query]

    def get_cmd_to_test(self):
        cmd = import_v1_files_to_s3.Command()
        cmd.file_prefix = "test_query_prefix"
        cmd.db = OracleDBProcessor(100, ["test_query"], 1)
        return cmd

    def test_get_query_last_run_key(self):
        assert import_v1_files_to_s3.get_query_last_run_key("TEST") == "TEST-last-run.json"

    def test_get_start_from_datetime_ignore_true(self):
        result = self.cmd.get_query_parameters(self.test_query, True)
        assert result == {"created_datetime": DEFAULT_FILE_CREATED_DATETIME}

    @mock.patch(
        "data_migration.management.commands.import_v1_files_to_s3.Command.get_last_run_data"
    )
    def test_get_start_from_datetime_ignore_false(self, mock_get_last_run_file):
        mock_get_last_run_file.return_value = {"created_datetime": CREATED_DATETIME_ALT}
        result = self.cmd.get_query_parameters(self.test_query, False)
        assert result == {"created_datetime": CREATED_DATETIME_ALT}

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
    @mock.patch(
        "data_migration.management.commands.import_v1_files_to_s3.s3_web.upload_file_obj_to_s3"
    )
    @mock.patch.object(OracleDBProcessor, "execute_query")
    def test_process_query_and_upload(self, mock_execute_query, mock_upload_file):
        fake_db_rows = [
            {
                "BLOB_DATA": "blob",
                "PATH": "testfile.txt",
                "CREATED_DATETIME": datetime.strptime(CREATED_DATETIME_ALT, "%Y-%m-%d %H:%M:%S"),
            },
            {
                "BLOB_DATA": "blob2",
                "PATH": "testfile2.txt",
                "CREATED_DATETIME": datetime.strptime(CREATED_DATETIME_ALT, "%Y-%m-%d %H:%M:%S"),
            },
        ]
        mock_upload_file.return_value = None
        mock_execute_query.return_value.__enter__.return_value = iter(fake_db_rows)

        result = self.cmd.process_query_and_upload(
            self.cmd.db.QUERIES[0],
            {"created_datetime": DEFAULT_FILE_CREATED_DATETIME},
            len(fake_db_rows),
        )
        assert result == {
            "created_datetime": "2023-01-01 01:00:00",
            "file_prefix": "test_query_prefix",
            "finished_at": "2023-01-01 01:00:00",
            "number_of_files_processed": len(fake_db_rows),
            "number_of_files_to_be_processed": len(fake_db_rows),
            "query_name": "test_query",
            "started_at": "2023-01-01 01:00:00",
        }

    @freezegun.freeze_time(CREATED_DATETIME_ALT)
    @mock.patch(
        "data_migration.management.commands.import_v1_files_to_s3.s3_web.upload_file_obj_to_s3"
    )
    @mock.patch.object(OracleDBProcessor, "execute_query")
    def test_process_query_and_upload_no_data(self, mock_execute_query, mock_upload_file):
        fake_db_rows = []
        mock_upload_file.return_value = None
        mock_execute_query.return_value.__enter__.return_value = iter(fake_db_rows)
        result = self.cmd.process_query_and_upload(
            self.cmd.db.QUERIES[0],
            {"created_datetime": DEFAULT_FILE_CREATED_DATETIME},
            len(fake_db_rows),
        )
        assert result == {
            "created_datetime": "2013-01-01 01:00:00",
            "file_prefix": "test_query_prefix",
            "finished_at": "2023-01-01 01:00:00",
            "number_of_files_processed": len(fake_db_rows),
            "number_of_files_to_be_processed": len(fake_db_rows),
            "query_name": "test_query",
            "started_at": "2023-01-01 01:00:00",
        }

    @freezegun.freeze_time(CREATED_DATETIME_ALT)
    @mock.patch("data_migration.management.commands.import_v1_files_to_s3.s3_web.put_object_in_s3")
    @mock.patch("data_migration.management.commands.import_v1_files_to_s3.s3_web.get_file_from_s3")
    @mock.patch.object(OracleDBProcessor, "execute_query")
    @mock.patch.object(OracleDBProcessor, "execute_count_query")
    def test_process_queries(
        self,
        mock_execute_count_query,
        mock_execute_query,
        mock_get_file_from_s3,
        mock_put_object_in_s3,
    ):
        mock_get_file_from_s3.return_value = b'{"created_datetime": "2023-05-02 12:00:00"}'
        mock_put_object_in_s3.return_value = None
        mock_execute_count_query.return_value = 10, 1000
        mock_execute_query.return_value.__enter__.return_value = iter([])

        self.cmd.process_queries(False, False)

        assert mock_execute_count_query.called is True
        assert mock_execute_query.called is True
        assert mock_get_file_from_s3.called is True
        assert mock_put_object_in_s3.called is True
        mock_put_object_in_s3.assert_called_once_with(
            json.dumps(
                {
                    "number_of_files_to_be_processed": 10,
                    "number_of_files_processed": 0,
                    "query_name": "test_query",
                    "file_prefix": "test_query_prefix",
                    "started_at": "2023-01-01 01:00:00",
                    "created_datetime": "2023-05-02 12:00:00",
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
            "file_prefix": "test_query_prefix",
            "number_of_files_processed": 0,
            "number_of_files_to_be_processed": 123,
            "query_name": "test_query",
            "started_at": "2023-01-01 01:00:00",
            "created_datetime": "2023-05-02 12:00:00",
        }


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
