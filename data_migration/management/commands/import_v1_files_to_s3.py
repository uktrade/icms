import datetime
import json
from typing import IO, Any

from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand
from tqdm import tqdm

from data_migration.management.commands.config.run_order import QueryModel
from data_migration.management.commands.utils.db_processor import (
    AVAILABLE_QUERIES,
    OracleDBProcessor,
)
from data_migration.utils.format import pretty_print_file_size
from web.utils import s3 as s3_web

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

REQUIRED_QUERY_PARAMETERS = ["created_datetime"]


def get_query_last_run_key(query_name: str) -> str:
    return f"{query_name}-last-run.json"


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            help="Limit queries to only return a set number of rows",
            type=int,
            default=None,
        )
        parser.add_argument(
            "--ignore-last-run",
            help="Ignore the data in the last run json file",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "--queries",
            help="Specify which queries to run, defaults to all available queries",
            nargs="+",
            choices=AVAILABLE_QUERIES,
            type=str,
            default=None,
        )
        parser.add_argument(
            "--s3-file-prefix",
            help="Prefix for all files when adding to s3 ie. a folder",
            type=str,
            default="",
        )
        parser.add_argument(
            "--number-of-rows",
            help="Number of rows to select in each batch default (10000)",
            type=int,
            default=10000,
        )
        parser.add_argument(
            "--count-only",
            help="Retrieves a count of number of files that will be processed per query",
            action="store_true",
            default=False,
        )

    def get_db(self, options: dict) -> OracleDBProcessor:
        """Returns a DB processor that facilitates executing database queries on the v1 oracle database."""
        return OracleDBProcessor(options["limit"], options["queries"], options["number_of_rows"])

    def handle(self, *args: Any, **options: Any) -> None:
        self.db = self.get_db(options)
        self.file_prefix = options["s3_file_prefix"]
        self.process_queries(options["ignore_last_run"], options["count_only"])

    def upload_file_obj_to_s3(self, _file_obj: IO[Any], _key: str) -> None:
        """Uploads a file to s3 adding a prefix to the file name (key) if required."""
        if self.file_prefix:
            _key = f"{self.file_prefix}/{_key}"
        s3_web.upload_file_obj_to_s3(_file_obj, _key)

    def get_initial_run_data_dict(
        self, query_model: QueryModel, query_parameters: dict, number_of_files_to_be_processed: int
    ) -> dict:
        """Returns a dictionary containing summary details of the current run for the given query."""
        return {
            "number_of_files_to_be_processed": number_of_files_to_be_processed,
            "number_of_files_processed": 0,
            "query_name": query_model.query_name,
            "file_prefix": self.file_prefix,
            "started_at": datetime.datetime.now().strftime(DATETIME_FORMAT),
        } | query_parameters

    def process_query_and_upload(
        self, query_model: QueryModel, query_parameters: dict, row_count: int
    ) -> dict[str, Any]:
        """Returns summary details of the last time the query was run including date time of
        last file processed (created_datetime) and parameters provided at runtime.

        For a given query
         - Selects all files to be added to s3
         - Uploads blob file data to s3
        """
        number_of_files_to_be_processed = min(row_count, self.db.limit or row_count)
        data_dict = self.get_initial_run_data_dict(
            query_model,
            query_parameters,
            number_of_files_to_be_processed,
        )

        pbar = tqdm(total=number_of_files_to_be_processed, desc=query_model.query_name)

        sql = self.db.get_sql(query_model)
        with self.db.execute_query(sql, query_parameters) as rows:
            try:
                while True:
                    obj = next(rows)
                    self.upload_file_obj_to_s3(obj["BLOB_DATA"], obj["PATH"])
                    pbar.update(1)
                    data_dict["number_of_files_processed"] = pbar.n
                    data_dict["created_datetime"] = obj["CREATED_DATETIME"].strftime(
                        DATETIME_FORMAT
                    )
            except StopIteration:
                pass
        pbar.close()
        data_dict["finished_at"] = datetime.datetime.now().strftime(DATETIME_FORMAT)
        return data_dict

    def process_queries(self, ignore_last_run: bool, count_only: bool) -> None:
        """For each of the specified queries in turn
        - Retrieves the summary details of last time (query parameters) the query was run
        - Retrieves and prints the count of the remaining files to be processed
        - Selects all files to be added to s3
        - Uploads blob file data to s3
        - Writes summary details of files processed (last run data) to s3
        """
        total_file_count = 0
        total_file_size = 0
        for query_model in self.db.get_query_list():
            query_parameters = self.get_query_parameters(query_model, ignore_last_run)

            file_count, file_size = self.db.execute_count_query(query_model, query_parameters)
            total_file_count += file_count
            total_file_size += file_size

            self.stdout.write(
                f"{query_model.query_name}: {file_count} files ({pretty_print_file_size(file_size)})"
            )

            if not count_only and file_count > 0:
                last_file_processed = self.process_query_and_upload(
                    query_model, query_parameters, file_count
                )
                self.write_run_data_to_s3(last_file_processed)
        self.stdout.write(
            f"\nTotal number of files to be uploaded: {total_file_count} ({pretty_print_file_size(total_file_size)})"
        )

    def get_query_parameters(self, query_model: QueryModel, ignore_last_run: bool) -> dict:
        """Returns all required query parameters."""
        if ignore_last_run:
            return query_model.parameters
        last_run_data = self.get_last_run_data(query_model)
        if not last_run_data:
            return query_model.parameters

        parameters = {}
        for _param in REQUIRED_QUERY_PARAMETERS:
            parameters[_param] = last_run_data[_param]
        return parameters

    def write_run_data_to_s3(self, result: dict[str, Any]) -> None:
        """Writes a (json) file to s3, which contains the details of the completed or partial run."""
        data = json.dumps(result)
        s3_web.put_object_in_s3(data, get_query_last_run_key(result["query_name"]))
        self.stdout.write(data)

    def get_last_run_data(self, query_model: QueryModel) -> dict:
        """Returns a dictionary of details of the last time the query was run.

        Attempts to retrieve a (json) file from s3 for a given query that contains summary details from
        the last time the query was run. If the file is not present an empty dict is returned.
        """
        file_name = get_query_last_run_key(query_model.query_name)
        try:
            file_blob = s3_web.get_file_from_s3(file_name)
            _data = json.loads(file_blob.decode())
        except ClientError:
            _data = {}
        return _data
