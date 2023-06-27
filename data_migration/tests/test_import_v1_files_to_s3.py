import io
import json
from datetime import datetime
from unittest import mock

import freezegun
from botocore.exceptions import ClientError

from data_migration.management.commands import import_v1_files_to_s3
from data_migration.management.commands.utils.db_processor import OracleDBProcessor

CREATED_DATETIME_ALT = "2023-01-01 01:00:00"


def test_get_query_last_run_key():
    assert import_v1_files_to_s3.get_query_last_run_key("TEST") == "TEST-last-run.json"


def test_get_default_last_run_data():
    assert import_v1_files_to_s3.get_default_last_run_data("TEST") == {
        "created_datetime": import_v1_files_to_s3.DEFAULT_CREATED_DATE_TIME,
        "query_name": "TEST",
    }


def get_cmd_to_test():
    query_dict = {"query_name": "test_query", "query": "select * from test_query_table"}
    cmd = import_v1_files_to_s3.Command()
    cmd.file_prefix = "test_query_prefix"
    cmd.db = OracleDBProcessor(100, ["test_query"], 1)
    cmd.db.QUERIES = [query_dict]
    return cmd


def test_get_start_from_datetime_ignore_true():
    cmd = import_v1_files_to_s3.Command()
    result = cmd.get_start_from_datetime(True, "test_query")
    assert result == import_v1_files_to_s3.DEFAULT_CREATED_DATE_TIME


@mock.patch("data_migration.management.commands.import_v1_files_to_s3.Command.get_last_run_data")
def test_get_start_from_datetime_ignore_false(mock_get_last_run_file):
    mock_get_last_run_file.return_value = {"created_datetime": CREATED_DATETIME_ALT}
    cmd = import_v1_files_to_s3.Command()
    result = cmd.get_start_from_datetime(False, "test_query")
    assert result == CREATED_DATETIME_ALT


@mock.patch("web.utils.s3.get_s3_client")
def test_get_last_run_data(mock_get_client):
    mock_get_client.return_value = FakeS3Client(b'{"text" : "hello"}')
    cmd = import_v1_files_to_s3.Command()
    result = cmd.get_last_run_data("test_query")
    assert result == {"text": "hello"}


@mock.patch("web.utils.s3.get_s3_client")
def test_get_last_run_data_when_file_does_not_exist(mock_get_client):
    mock_get_client.return_value = FakeS3Client(None, raise_exception=True)
    cmd = import_v1_files_to_s3.Command()
    result = cmd.get_last_run_data("test_query")
    assert result == import_v1_files_to_s3.get_default_last_run_data("test_query")


@freezegun.freeze_time(CREATED_DATETIME_ALT)
@mock.patch("data_migration.management.commands.import_v1_files_to_s3.s3_web.upload_file_obj_to_s3")
@mock.patch.object(OracleDBProcessor, "execute_query")
def test_process_query_and_upload(mock_execute_query, mock_upload_file):
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

    cmd = get_cmd_to_test()
    result = cmd.process_query_and_upload(
        cmd.db.QUERIES[0], import_v1_files_to_s3.DEFAULT_CREATED_DATE_TIME, len(fake_db_rows)
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
@mock.patch("data_migration.management.commands.import_v1_files_to_s3.s3_web.upload_file_obj_to_s3")
@mock.patch.object(OracleDBProcessor, "execute_query")
def test_process_query_and_upload_no_data(mock_execute_query, mock_upload_file):
    fake_db_rows = []
    mock_upload_file.return_value = None
    mock_execute_query.return_value.__enter__.return_value = iter(fake_db_rows)
    cmd = get_cmd_to_test()
    result = cmd.process_query_and_upload(
        cmd.db.QUERIES[0], import_v1_files_to_s3.DEFAULT_CREATED_DATE_TIME, len(fake_db_rows)
    )
    assert result == {
        "created_datetime": "1900-12-13 09:39:21",
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
    mock_execute_count_query, mock_execute_query, mock_get_file_from_s3, mock_put_object_in_s3
):
    mock_get_file_from_s3.return_value = b'{"created_datetime": "2023-05-02 12:00:00"}'
    mock_put_object_in_s3.return_value = None
    mock_execute_count_query.return_value = 10
    mock_execute_query.return_value.__enter__.return_value = iter([])

    cmd = get_cmd_to_test()
    cmd.process_queries(False, False)

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
                "created_datetime": "2023-05-02 12:00:00",
                "started_at": "2023-01-01 01:00:00",
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
    mock_execute_count_query, mock_execute_query, mock_get_file_from_s3, mock_put_object_in_s3
):
    mock_get_file_from_s3.return_value = None
    mock_put_object_in_s3.return_value = None
    mock_execute_count_query.return_value = 10
    mock_execute_query.return_value.__enter__.return_value = iter([])

    cmd = get_cmd_to_test()
    cmd.process_queries(True, True)

    assert mock_get_file_from_s3.called is False
    assert mock_execute_count_query.called is True
    assert mock_execute_query.called is False
    assert mock_put_object_in_s3.called is False


@freezegun.freeze_time(CREATED_DATETIME_ALT)
def test_get_initial_run_data_dict():
    cmd = import_v1_files_to_s3.Command()
    cmd.file_prefix = "test_query_prefix"
    result = cmd.get_initial_run_data_dict("test_query", 123, "2023-05-02 12:00:00")
    assert result == {
        "created_datetime": "2023-05-02 12:00:00",
        "file_prefix": "test_query_prefix",
        "number_of_files_processed": 0,
        "number_of_files_to_be_processed": 123,
        "query_name": "test_query",
        "started_at": "2023-01-01 01:00:00",
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
