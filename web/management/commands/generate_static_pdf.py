from io import BytesIO
from typing import Any

from django.core.management.base import BaseCommand
from guardian.utils import get_anonymous_user

from web.models import File
from web.types import DocumentTypes
from web.utils.pdf import StaticPdfGenerator
from web.utils.pdf.utils import cfs_cover_letter_key_filename
from web.utils.s3 import upload_file_obj_to_s3


class Command(BaseCommand):
    help = """Generates the static CFS Cover Letter PDF document and uploads to S3"""

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("Generating CFS cover letter.")

        file_obj = BytesIO()
        pdf_gen = StaticPdfGenerator(DocumentTypes.CFS_COVER_LETTER)
        pdf_gen.get_pdf(target=file_obj)
        file_obj.seek(0)
        key, filename = cfs_cover_letter_key_filename()

        self.stdout.write("Uploading cover letter to S3.")
        file_size = upload_file_obj_to_s3(file_obj, key)

        try:
            self.stdout.write("Fetching file object from File model.")
            document = File.objects.get(filename=filename, path=key)

            self.stdout.write("Updating file object.")
            document.file_size = file_size
            document.save()

        except File.DoesNotExist:
            self.stdout.write("No file object found. Creating.")
            anon_user = get_anonymous_user()

            File.objects.create(
                is_active=True,
                filename=filename,
                content_type="application/pdf",
                file_size=file_size,
                path=key,
                created_by=anon_user,
            )

        self.stdout.write("Done.")
