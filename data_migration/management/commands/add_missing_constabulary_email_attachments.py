import argparse
import json
from typing import Any

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder

from data_migration import models as dm
from data_migration.management.commands.utils.db_processor import OracleDBProcessor
from data_migration.utils.format import adjust_icms_v1_datetime
from web.models import File
from web.utils import s3 as s3_web

constabulary_email_files_query = """
SELECT
fv.fft_id file_target_id
, x.filename
, x.content_type
, x.file_size
, fv.create_start_datetime created_datetime
, fv.create_by_wua_id created_by_id
, 'consabulary_email_attachments_deleted/' || fv.id || '-' || x.filename path
, sld.blob_data
FROM DECMGR.FILE_VERSIONS fv
CROSS JOIN XMLTABLE('/*'
 PASSING metadata_xml
 COLUMNS
  filename VARCHAR2(4000) PATH '/file-metadata/filename/text()'
  , content_type VARCHAR2(4000) PATH '/file-metadata/content-type/text()'
  , file_size NUMBER PATH '/file-metadata/size/text()'
) x
INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(fv.secure_lob_ref).id
WHERE fft_id = :file_target_id
"""


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--dry-run",
            help="Dry run without actually doing anything",
            action="store_true",
        )

    def get_db(self) -> OracleDBProcessor:
        """Returns a DB processor that facilitates executing database queries on the v1 oracle database."""
        return OracleDBProcessor(100, ["Constabulary Email Missing Attachments"], 100)

    def handle(self, *args: Any, **options: Any) -> None:
        self.dry_run = options["dry_run"]
        self.add_files_constabulary_email_attachments()

    def add_files_constabulary_email_attachments(self) -> None:
        """Finds the constabulary emails with missing attachments in the data migration tables
        - Fetches the missing files from the V1 database
        - Uploads missing attachment files to S3
        - Adds the file data to V2 db
        - Associates the file data with the relevant case email
        """

        sql = constabulary_email_files_query
        db = self.get_db()

        qs = (
            dm.ConstabularyEmailAttachments.objects.filter(file_target__files__isnull=True)
            .values_list("file_target_id", flat=True)
            .distinct()
        )

        for obj in qs:
            with db.execute_query(sql, {"file_target_id": obj.file_target_id}) as rows:
                try:
                    while True:
                        row = next(rows)
                        self.stdout.write(f"Processing file: {row['FILE_TARGET_ID']}")
                        created = self.add_file_to_db(row)
                        if created:
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

    def add_file_to_db(self, row: dict[str, Any]) -> bool:
        """Finds the relevant case email in the V2 database add adds the file attachment data."""
        file_data = dict(
            filename=row["FILENAME"],
            content_type=row["CONTENT_TYPE"],
            file_size=row["FILE_SIZE"],
            path=row["PATH"],
            created_datetime=adjust_icms_v1_datetime(row["CREATED_DATETIME"]),
            created_by_id=row["CREATED_BY_ID"],
        )
        if self.dry_run:
            self.stdout.write(json.dumps(file_data, indent=2, cls=DjangoJSONEncoder))
            created = True
        else:
            _, created = File.objects.get_or_create(**file_data)
        return created
