import argparse
from io import BytesIO
from pathlib import Path
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

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--output",
            choices=["s3", "disk"],
            default="s3",
            help="Specify preffered output s3 / disk. Disk saves documents to output_documents folder. Defualts to S3.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        output = options["output"]

        if output == "disk":
            self.output_to_disk()
        else:
            self.output_to_s3()

        self.stdout.write("Done.")

    def generate_pdf(self) -> BytesIO:
        """Generate the pdf bytes object"""

        self.stdout.write("Generating CFS cover letter.")
        file_obj = BytesIO()
        pdf_gen = StaticPdfGenerator(DocumentTypes.CFS_COVER_LETTER)
        pdf_gen.get_pdf(target=file_obj)
        file_obj.seek(0)

        return file_obj

    def output_to_disk(self) -> None:
        """Save the generated pdf to output_documents"""

        file_obj = self.generate_pdf()
        _, filename = cfs_cover_letter_key_filename()

        output_documents = Path(".") / "output_documents/"
        output_documents.mkdir(parents=True, exist_ok=True)
        output_file = output_documents / filename

        self.stdout.write("Saving the pdf to output_documents.")

        with open(output_file, "wb") as f:
            f.write(file_obj.getvalue())
            self.stdout.write(f"Saved the pdf to output_documents/{filename}")

    def output_to_s3(self) -> None:
        """Upload the generated pdf to S3"""

        file_obj = self.generate_pdf()
        key, filename = cfs_cover_letter_key_filename()

        self.stdout.write(f"Uploading cover letter to S3. {key}")

        file_size = upload_file_obj_to_s3(file_obj, key)
        anon_user = get_anonymous_user()

        self.stdout.write("Fetching file object from File model.")

        document, created = File.objects.get_or_create(
            filename=filename,
            path=key,
            defaults={
                "is_active": True,
                "content_type": "application/pdf",
                "file_size": file_size,
                "created_by": anon_user,
            },
        )

        if created:
            self.stdout.write("No file object found. Created.")
        else:
            self.stdout.write("Updating file object.")

            document.file_size = file_size
            document.save()
