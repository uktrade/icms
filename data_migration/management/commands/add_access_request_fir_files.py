import argparse
import json
import pathlib
from typing import Any

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
from whitenoise.media_types import default_types  # type: ignore

from data_migration import models as dm
from data_migration.management.commands.utils.db_processor import OracleDBProcessor
from data_migration.utils.format import adjust_icms_v1_datetime
from web.models import AccessRequest, File
from web.utils import s3 as s3_web

access_request_fir_files_query = """
SELECT
  sld.BLOB_DATA
, EXTRACTVALUE(fv.metadata_xml, '/file-metadata/size') file_size
, 'access_request_docs/' || fv.file_id || '-' || fv.filename path
, fv.filename
, fv.content_type
, xir.requested_datetime as fir_requested_datetime
, xir.responded_datetime as fir_responded_datetime
, xir.request_subject as fir_request_subject
, fv.created_by_wua_id AS created_by_id
, fv.created_datetime
, iar.id as access_request_id
, iar.request_reference
, sld.id as secure_lob_ref_id
FROM impmgr.importer_access_requests iar
CROSS JOIN XMLTABLE('
  for $g1 in /IMPORTER_ACCESS_REQUEST/RFIS/RFI_LIST/RFI | <null/>
  where /IMPORTER_ACCESS_REQUEST/RFIS/RFI_LIST/RFI and $g1/RFI_ID/text()
  return
  <root>
    <rfi_uref>{{$g1/RFI_ID/text()}}IARRFI</rfi_uref>
    <rfi_id>{{$g1/RFI_ID/text()}}</rfi_id>
  </root>
  '
  PASSING iar.xml_data
  COLUMNS
    rfi_uref VARCHAR2(4000) PATH '/root/rfi_uref/text()'
    , rfi_id NUMBER PATH '/root/rfi_id/text()'
) x
INNER JOIN DOCLIBMGR.VW_FOLDERS vf ON vf.SECONDARY_DATA_UREF = x.rfi_uref
INNER JOIN DOCLIBMGR.REVISION_FOLDERS_FILES rff ON vf.F_ID = rff.F_ID
INNER JOIN DOCLIBMGR.VW_FILE_REVISIONS fv ON fv.FILE_ID = rff.FILE_ID
INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(fv.secure_lob_ref).id
INNER JOIN IMPMGR.XVIEW_IAR_RFIS xir ON x.rfi_id = xir.rfi_id AND xir.requested_datetime IS NOT NULL
{where}
ORDER BY sld.id
"""


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--dry-run",
            help="Dry run without actually doing anything",
            action="store_true",
        )
        parser.add_argument(
            "--limit",
            help="Limit db queries to only return a set number of rows",
            type=int,
            default=None,
        )
        parser.add_argument(
            "--secure_lob_ref_id",
            help="Specify the secure lob ref id to start processing from",
            type=int,
            default=0,
        )

    def get_db(self, limit: int) -> OracleDBProcessor:
        """Returns a DB processor that facilitates executing database queries on the v1 oracle database."""
        return OracleDBProcessor(limit, ["Access Request FIR Files"], 100)

    def handle(self, *args: Any, **options: Any) -> None:
        self.dry_run = options["dry_run"]
        self.add_files_access_request_firs(options["limit"], options["secure_lob_ref_id"])

    def add_files_access_request_firs(self, limit: int, start_at_secure_lob_ref_id: int) -> None:
        """Retrieves access request, further information request (fir) data from V1 oracle database
        - Uploads missing attachment files to S3
        - Adds the file data to V2 db
        - Associates the file data with the relevant access request fir
        """

        where = ""
        query_parameters = {}
        if start_at_secure_lob_ref_id != 0:
            # The where clause slows the query down considerably so is only added
            # when a secure lob ref id is specified.
            query_parameters = {"SECURE_LOB_REF_ID": start_at_secure_lob_ref_id}
            where = "WHERE sld.id > :secure_lob_ref_id"

        sql = access_request_fir_files_query.format(where=where)

        db = self.get_db(limit)
        number_of_files, _ = db.execute_cumulative_query(db.add_count_to_sql(sql), query_parameters)
        self.stdout.write(f"Processing {number_of_files} files")
        with db.execute_query(sql, query_parameters) as rows:
            try:
                while True:
                    row = next(rows)
                    self.stdout.write(f"Processing file: {row['SECURE_LOB_REF_ID']}")
                    self.add_file_to_db(row)
                    self.upload_file_to_s3(row)
            except StopIteration:
                pass

    def upload_file_to_s3(self, row: dict[str, Any]) -> None:
        """Uploads fir attachment file to S3."""
        file_size_limit = 5 * 1024**2
        if self.dry_run:
            return
        if row["FILE_SIZE"] and int(row["FILE_SIZE"]) > file_size_limit:
            s3_web.upload_file_obj_to_s3_in_parts(row["BLOB_DATA"], row["PATH"])
        else:
            s3_web.upload_file_obj_to_s3(row["BLOB_DATA"], row["PATH"])

    def add_file_to_db(self, row: dict[str, Any]) -> None:
        """Finds the relevant access request fir in the V2 database add adds the fir file attachment data."""
        access_request_pk = dm.AccessRequest.objects.get(iar_id=row["ACCESS_REQUEST_ID"]).pk
        ar_data = dict(reference=row["REQUEST_REFERENCE"], pk=access_request_pk)
        if self.dry_run:
            self.stdout.write(json.dumps(ar_data, indent=2, cls=DjangoJSONEncoder))
        access_request = AccessRequest.objects.get(**ar_data)

        fir_data = dict(
            request_subject=row["FIR_REQUEST_SUBJECT"],
            requested_datetime=adjust_icms_v1_datetime(row["FIR_REQUESTED_DATETIME"]),
            response_datetime=adjust_icms_v1_datetime(row["FIR_RESPONDED_DATETIME"]),
        )
        if self.dry_run:
            self.stdout.write(json.dumps(fir_data, indent=2, cls=DjangoJSONEncoder))
        fir = access_request.further_information_requests.get(**fir_data)

        file_data = dict(
            filename=row["FILENAME"],
            content_type=self.get_content_type(row["FILENAME"], row["CONTENT_TYPE"]),
            file_size=row["FILE_SIZE"],
            path=row["PATH"],
            created_datetime=adjust_icms_v1_datetime(row["CREATED_DATETIME"]),
            created_by_id=row["CREATED_BY_ID"],
        )
        if self.dry_run:
            self.stdout.write(json.dumps(file_data, indent=2, cls=DjangoJSONEncoder))
        else:
            file_obj = File.objects.create(**file_data)
            fir.files.add(file_obj)

    def get_content_type(self, file_name: str, content_type: str) -> str:
        if content_type:
            return content_type
        file_name = file_name.lower()
        extension = pathlib.Path(file_name).suffix
        return default_types()[extension]
