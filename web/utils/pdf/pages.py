import io
from typing import Any

import pypdf
from reportlab.lib.pagesizes import A4, portrait
from reportlab.pdfgen import canvas


def format_cfs_pages(pdf_data: bytes, context: dict[str, Any]) -> bytes:
    """Function to add page numbers and running headers and footers to CFS documents
    Creates new blank pages with only the header and footer content and merges with
    the original document."""

    reader = pypdf.PdfReader(io.BytesIO(pdf_data))
    writer = pypdf.PdfWriter()

    issue_date = context["issue_date"]
    reference = context["reference"]

    left_margin = 73
    top_margin = 780
    page_total = len(reader.pages)
    for page_number, page in enumerate(reader.pages):
        packet = io.BytesIO()
        new_page = canvas.Canvas(packet, pagesize=portrait(A4))
        new_page.setFont("Helvetica", 10)
        new_page.drawRightString(525, top_margin, f"Page {page_number + 1} of {page_total}")
        new_page.drawString(left_margin, top_margin, reference)

        if page_number == 0:
            new_page.setFontSize(12)
            new_page.drawString(left_margin, 90, "Date issued:")
            new_page.drawString(left_margin, 76, issue_date)

        else:
            new_page.drawString(
                left_margin, 52, f"This schedule is only valid with Certificate {reference}"
            )
            new_page.drawString(left_margin, 28, f"Date issued: {issue_date}")

        new_page.save()

        packet.seek(0)
        new_pdf = pypdf.PdfReader(packet)
        page.merge_page(new_pdf.pages[0])
        writer.add_page(page)

    with io.BytesIO() as bytes_stream:
        writer.write(bytes_stream)
        return bytes_stream.getvalue()
