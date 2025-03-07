import datetime as dt
import json
from functools import cached_property
from pathlib import Path

from django.conf import settings
from freezegun import freeze_time
from pdf2image import convert_from_bytes
from PIL import Image, ImageChops

from web.domains.case.models import ApplicationBase
from web.utils.pdf import PdfGenerator

BENCHMARK_PDF_DIRECTORY = (
    Path(settings.BASE_DIR)
    / "web"
    / "tests"
    / "utils"
    / "pdf"
    / "test_visual_regression"
    / "benchmark_pdfs"
)

date_created_json_file = BENCHMARK_PDF_DIRECTORY / "dates_created.json"


class BaseTestPDFVisualRegression:
    """Base class for visual regression tests for PDFs.

    Every subclass of this class corresponds to a different application type


    The process looks something like this:

    1. Every time we update the PDF styling, we generate a new set of benchmark PDFs.
    2. When we run the tests, we generate the PDFs again and compare them to the benchmark PDFs.
    3. Both the generated PDFs and the benchmark PDFs are converted to images
    4. We compare the images pixel by pixel to see if there are any differences.
    5. We allow for a small number of pixels to be different, just to account for any rendering differences.
    6. If the number of different pixels is higher than the tolerable difference, the test fails.
    """

    application: ApplicationBase = None
    # we allow for 5 pixels of difference just to account for any rendering differences
    tolerable_difference: int = 5
    benchmark_pdf_image_file_path: str = None

    def get_generator_kwargs(self) -> dict[str, any]:
        return {
            "application": self.application,
        }

    def get_generator(self) -> PdfGenerator:
        """Gets the PdfGenerator object with the relevant kwargs."""
        return PdfGenerator(**self.get_generator_kwargs())

    def get_pdf(self) -> bytes:
        """Get the generated PDF as bytes."""
        return self.get_generator().get_pdf()

    def test_pdf(self, *args, **kwargs):
        """Test the generated PDF against the benchmark PDF.

        This needs to be subclassed so that we can pass the relevant application fixture to the test method.
        """
        raise NotImplementedError(
            "You must implement at least this method in a subclass. Assign the application fixture "
            "to self.application and call self.compare_pdf() in this method."
        )

    @property
    def benchmark_pdf_image(self) -> list[Image.Image]:
        """Get the benchmark PDF image as a list of PIL.Image.Image objects."""
        return convert_from_bytes(
            (BENCHMARK_PDF_DIRECTORY / self.benchmark_pdf_image_file_path).read_bytes()
        )

    @cached_property
    def benchmark_pdf_creation_date(self) -> dt.datetime:
        """Get the creation date of the benchmark PDF.

        This is used to freeze time when generating the PDFs. so they look the same."""
        date_stamp_dict = json.loads(date_created_json_file.read_text())
        return dt.datetime.fromisoformat(date_stamp_dict[self.benchmark_pdf_image_file_path])

    def compare_pdf(self) -> None:
        benchmark_pdf_image = self.benchmark_pdf_image

        with freeze_time(self.benchmark_pdf_creation_date):
            # freezing time here to ensure that the generated PDFs have the same date as the benchmark PDFs.
            # different dates cause different headers and footers in the PDFs, which would cause the test to fail.
            generated_pdf_image = convert_from_bytes(self.get_pdf())

            # save the generated pdfs for debugging if required
            if settings.SAVE_GENERATED_PDFS:
                for page, image in enumerate(generated_pdf_image):
                    output_file = (
                        settings.BASE_DIR
                        / "generated_pdfs"
                        / self.__class__.__name__
                        / f"{self.benchmark_pdf_image_file_path}_generated_page_{page}.png"
                    )
                    output_file.parent.mkdir(exist_ok=True, parents=True)
                    with output_file.open("wb") as f:
                        image.save(f, "PNG")

        # both pdfs should at least have the same number of pages
        assert len(generated_pdf_image) == len(benchmark_pdf_image)

        for page, (generated_page, benchmark_page) in enumerate(
            zip(generated_pdf_image, benchmark_pdf_image)
        ):
            # compare the images pixel by pixel
            diff = ImageChops.difference(generated_page, benchmark_page)

            # Save the diff image for debugging if required
            if settings.SAVE_GENERATED_PDFS:
                output_file = (
                    settings.BASE_DIR
                    / "generated_pdfs"
                    / self.__class__.__name__
                    / f"{self.benchmark_pdf_image_file_path}_diff_{page}.png"
                )
                with output_file.open("wb") as f:
                    diff.save(f, "PNG")

            # get a quantifiable difference metric
            diff_metric = len(set(diff.getdata()))

            # we're expecting a number lower than the tolerable difference
            assert (
                diff_metric <= self.tolerable_difference
            ), f"Amount over difference: {diff_metric - self.tolerable_difference}"
