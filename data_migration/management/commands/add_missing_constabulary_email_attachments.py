import argparse
import json
from typing import Any

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder

from data_migration import models as dm
from data_migration.management.commands.utils.db_processor import OracleDBProcessor
from data_migration.utils.format import adjust_icms_v1_datetime
from web.models import CaseEmail, File
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


beis_email_attachments_files = """
SELECT
  e.ca_id
  , e.email_body "body"
  , x.sent_datetime
  , x.target_id
  , x.select_flag
FROM impmgr.xview_cert_app_beis_emails e
INNER JOIN impmgr.certificate_app_details cad ON cad.id = e.cad_id
CROSS JOIN XMLTABLE('
  for $g1 in /*/CASE/BEIS_EMAILS/EMAIL_LIST/EMAIL | <null />
  where /*/CASE/BEIS_EMAILS/EMAIL_LIST/EMAIL and $g1/STATUS/text()
  return
  for $g2 in $g1/SEND/SUPPORTING_DOCUMENT_LIST/SUPPORTING_DOCUMENT | <null />
  where $g1/SEND/SUPPORTING_DOCUMENT_LIST/SUPPORTING_DOCUMENT and $g2/SELECT_FLAG[text()="true"]
  return
  <root>
    <email_id>{$g1/EMAIL_ID/text()}</email_id>
    <status>{$g1/STATUS/text()}</status>
    <sent_datetime>{$g1/SEND/SENT_DATETIME/text()}</sent_datetime>
    <target_id>{$g2/TARGET_ID/text()}</target_id>
    <select_flag>{$g2/SELECT_FLAG/text()}</select_flag>
  </root>
  '
  PASSING cad.xml_data
  COLUMNS
    email_id NUMBER PATH '/root/email_id/text()'
  , status VARCHAR2(4000) PATH '/root/status/text()'
  , sent_datetime VARCHAR2(4000) PATH '/root/sent_datetime/text()'
  , target_id VARCHAR2(4000) PATH '/root/target_id/text()'
  , select_flag VARCHAR2(4000) PATH '/root/select_flag/text()'
) x
WHERE e.status_control = 'C'
AND x.email_id = e.email_id
AND e.status <> ' DELETED'
ORDER BY e.cad_id, e.email_id
"""


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--dry-run",
            help="Dry run without actually doing anything",
            action="store_true",
        )

    def get_db(self, query_name: str) -> OracleDBProcessor:
        """Returns a DB processor that facilitates executing database queries on the v1 oracle database."""
        return OracleDBProcessor(100, [query_name], 100)

    def handle(self, *args: Any, **options: Any) -> None:
        self.dry_run = options["dry_run"]
        self.add_files_constabulary_email_attachments()

    def add_beis_email_attachments(self) -> None:
        """Finds the files attached to the BEIS emails V1 and links the attachments to CaseEmail in V2"""

        sql = beis_email_attachments_files
        db = self.get_db("BEIS Email Attachments")

        with db.execute_query(sql, {}) as rows:
            try:
                while True:
                    row = next(rows)
                    self.add_attachements_to_beis_email(row)
            except StopIteration:
                pass

    def add_attachments_to_beis_email(self, row: dict[str, Any]) -> None:
        email_data = dict(
            ca_id=row["CA_ID"],
            body=row["BODY"],
            status=row["STATUS"],
            sent_datetime=adjust_icms_v1_datetime(row["SENT_DATETIME"]),
            template_code=["CA_BEIS_EMAIL"],
        )

        dm_case_email = dm.CaseEmail.objects.get(**email_data)
        case_email = CaseEmail.objects.get(pk=dm_case_email.pk)
        app = case_email.export_applications.first().get_specific_model()

        dm_file_pks = dm.File.objects.filter(target_id=row["TARGET_ID"]).values_list(
            "pk", flat=True
        )
        files = app.supporting_documents.filter(pk__in=dm_file_pks)

        if self.dry_run:
            print(f"{app.reference} - Adding {files.count()} files to BEIS Email")
            return

        for file in files:
            case_email.attachments.add(file)

    def add_files_constabulary_email_attachments(self) -> None:
        """Finds the constabulary emails with missing attachments in the data migration tables
        - Fetches the missing files from the V1 database
        - Uploads missing attachment files to S3
        - Adds the file data to V2 db
        """

        sql = constabulary_email_files_query
        db = self.get_db("Missing Constabulary Email Attachments")

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
