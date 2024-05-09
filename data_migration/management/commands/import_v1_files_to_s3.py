import datetime as dt
import json
from typing import Any

from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand
from tqdm import tqdm

from data_migration.management.commands.config.run_order import QueryModel
from data_migration.management.commands.utils.db_processor import (
    AVAILABLE_QUERIES,
    QUERY_GROUPS,
    OracleDBProcessor,
)
from data_migration.utils.format import pretty_print_file_size
from web.utils import s3 as s3_web


def get_query_last_run_key(query_name: str) -> str:
    return f"{query_name}-last-run.json"


class Command(BaseCommand):
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batchsize",
            help="Number of results per db query batch",
            default=500,
            type=int,
        )
        parser.add_argument(
            "--run-data-batchsize",
            help="Save run data to s3 periodically after processing this number of files",
            type=int,
            default=100,
        )
        parser.add_argument(
            "--limit",
            help="Limit db queries to only return a set number of rows",
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
            help="Specify which queries to run by name or group alias (small/large), defaults to all available queries",
            nargs="+",
            choices=AVAILABLE_QUERIES + list(QUERY_GROUPS.keys()),
            type=str,
            default=None,
        )
        parser.add_argument(
            "--count-only",
            help="Retrieves a count of number of files that will be processed per query",
            action="store_true",
            default=False,
        )

    def get_db(self, options: dict) -> OracleDBProcessor:
        """Returns a DB processor that facilitates executing database queries on the v1 oracle database."""
        return OracleDBProcessor(options["limit"], options["queries"], options["batchsize"])

    def handle(self, *args: Any, **options: Any) -> None:
        self.run_data_batchsize = options["run_data_batchsize"]
        self.db = self.get_db(options)
        self.process_queries(options["ignore_last_run"], options["count_only"])

    def get_initial_run_data_dict(
        self, query_model: QueryModel, query_parameters: dict, number_of_files_to_be_processed: int
    ) -> dict:
        """Returns a dictionary containing summary details of the current run for the given query."""
        return {
            "number_of_files_to_be_processed": number_of_files_to_be_processed,
            "number_of_files_processed": 0,
            "query_name": query_model.query_name,
            "started_at": dt.datetime.now().strftime(self.DATETIME_FORMAT),
        } | query_parameters

    def process_query_and_upload(
        self, query_model: QueryModel, query_parameters: dict, row_count: int
    ) -> None:
        """Returns summary details of the last time the query was run including date time of
        last file processed (created_datetime) and parameters provided at runtime.

        For a given query
         - Selects all files to be added to s3
         - Uploads blob file data to s3, if the file is larger than 5 MiB the file is uploaded in chunks
        """
        number_of_files_to_be_processed = min(row_count, self.db.limit or row_count)
        data_dict = self.get_initial_run_data_dict(
            query_model,
            query_parameters,
            number_of_files_to_be_processed,
        )

        pbar = tqdm(total=number_of_files_to_be_processed, desc=query_model.query_name)
        file_size_limit = 5 * 1024**2
        sql = self.db.get_sql(query_model)
        with self.db.execute_query(sql, query_parameters) as rows:
            try:
                while True:
                    obj = next(rows)
                    if obj["FILE_SIZE"] > file_size_limit:
                        s3_web.upload_file_obj_to_s3_in_parts(obj["BLOB_DATA"], obj["PATH"])
                    else:
                        s3_web.upload_file_obj_to_s3(obj["BLOB_DATA"], obj["PATH"])
                    pbar.update(1)
                    self.save_run_data(data_dict, pbar.n, obj)
            except StopIteration:
                pass
        pbar.close()

    def should_save_run_data(
        self, number_of_files_processed: int, number_of_files_to_be_processed: int
    ) -> bool:
        """Returns True if the current run data (which maybe in progress) should be saved.

        - If no files have been processed don't save the file
        - If the run has completed save the file
        - If the run is in progress and the number of files is a divisible to an equal number of the SAVE_RUN_DATA
          value then save the file
        - All other circumstances don't save the file
        """
        if not number_of_files_processed:
            return False
        if number_of_files_processed == number_of_files_to_be_processed:
            return True
        if not number_of_files_processed % self.run_data_batchsize:
            return True
        return False

    def save_run_data(
        self, data_dict: dict, number_of_files_processed: int, last_file_processed: dict
    ) -> None:
        """If required save the run data including the created_datetime of the last file processed to s3"""
        if self.should_save_run_data(
            number_of_files_processed, data_dict["number_of_files_to_be_processed"]
        ):
            data_dict["number_of_files_processed"] = number_of_files_processed
            data_dict["created_datetime"] = last_file_processed["CREATED_DATETIME"].strftime(
                self.DATETIME_FORMAT
            )
            data_dict["finished_at"] = dt.datetime.now().strftime(self.DATETIME_FORMAT)
            data_dict["secure_lob_ref_id"] = last_file_processed["SECURE_LOB_REF_ID"]
            self.write_run_data_to_s3(data_dict)

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
                self.process_query_and_upload(query_model, query_parameters, file_count)
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
        parameters = query_model.parameters.copy()
        parameters[query_model.limit_by_field] = last_run_data[query_model.limit_by_field]
        return parameters

    def write_run_data_to_s3(self, result: dict[str, Any]) -> None:
        """Writes a (json) file to s3, which contains the details of the completed or partial run."""
        data = json.dumps(result)
        s3_web.put_object_in_s3(data, get_query_last_run_key(result["query_name"]))

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
