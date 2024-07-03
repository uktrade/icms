import datetime as dt
import json
from pathlib import Path

from freezegun import freeze_time
from pdf2image import convert_from_bytes
from PIL import Image, ImageChops

from web.domains.case.models import ApplicationBase
from web.utils.pdf import PdfGenerator

BENCHMARK_PDF_DIRECTORY = Path(__name__).parent / "benchmark_pdfs"

# load the date the benchmark PDFs were created, do this here to avoid loading it for every test
with open(BENCHMARK_PDF_DIRECTORY / "date_created.json") as f:
    d = json.load(f)
    date_benchmarks_created = dt.datetime.fromisoformat(d["date_created"])


class BaseTestPDFVisualRegression:
    application: ApplicationBase = None
    # we allow for 5 pixels of difference just to account for any rendering differences
    tolerable_difference: int = 5
    benchmark_pdf_image_file: str = None

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
            "You must implement this method in a subclass. Assign the application fixture to self.application and call self.compare_pdf() in this method."
        )

    @property
    def benchmark_pdf_image(self) -> list[Image.Image]:
        """Get the benchmark PDF image as a list of PIL.Image.Image objects."""
        return convert_from_bytes(
            (BENCHMARK_PDF_DIRECTORY / self.benchmark_pdf_image_file).read_bytes()
        )

    def compare_pdf(self) -> None:
        benchmark_pdf_image = self.benchmark_pdf_image

        with freeze_time(date_benchmarks_created):
            # freezing time here to ensure that the generated PDFs have the same date as the benchmark PDFs.
            # different dates cause different headers and footers in the PDFs, which would cause the test to fail.
            generated_pdf_image = convert_from_bytes(self.get_pdf())

        # both pdfs should at least have the same number of pages
        assert len(generated_pdf_image) == len(benchmark_pdf_image)

        for generated_page, benchmark_page in zip(generated_pdf_image, benchmark_pdf_image):
            # compare the images pixel by pixel
            diff = ImageChops.difference(generated_page, benchmark_page)

            # get a quantifiable difference metric
            diff_metric = len(set(diff.getdata()))

            # we're expecting a number lower than the tolerable difference
            assert diff_metric <= self.tolerable_difference
