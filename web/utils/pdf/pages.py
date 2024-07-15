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


def format_gmp_pages(pdf_data: bytes, context: dict[str, Any]) -> bytes:
    """Function to add page numbers and running headers and footers to GMP documents
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
        new_page.setFontSize(12)
        new_page.drawString(left_margin, 90, "Date issued:")
        new_page.drawString(left_margin, 76, issue_date)
        new_page.save()

        packet.seek(0)
        new_pdf = pypdf.PdfReader(packet)
        page.merge_page(new_pdf.pages[0])
        writer.add_page(page)

    with io.BytesIO() as bytes_stream:
        writer.write(bytes_stream)
        return bytes_stream.getvalue()


def format_com_pages(pdf_data: bytes) -> bytes:
    """Function to merge the first page containing only the footer with the following pages
    in CFS PDF documents."""

    reader = pypdf.PdfReader(io.BytesIO(pdf_data))
    writer = pypdf.PdfWriter()

    footer_page = reader.pages[0]

    for page in reader.pages[1:]:
        page.merge_page(footer_page)
        writer.add_page(page)

    with io.BytesIO() as bytes_stream:
        writer.write(bytes_stream)
        return bytes_stream.getvalue()


def format_wood_pages(pdf_data: bytes) -> bytes:
    reader = pypdf.PdfReader(io.BytesIO(pdf_data))
    writer = pypdf.PdfWriter()

    top_margin = 795
    left_margin = 66
    right_margin = 560
    page_total = len(reader.pages)
    for page_number, page in enumerate(reader.pages):
        packet = io.BytesIO()
        new_page = canvas.Canvas(packet, pagesize=portrait(A4))
        new_page.setFont("Helvetica-Bold", 10)
        new_page.drawRightString(184, top_margin, "EUROPEAN UNION")
        new_page.drawRightString(480, top_margin, "QUOTA AUTHORISATION")

        # Top of the page horizontal line
        new_page.line(left_margin, 791, right_margin, 791)

        if page_number == 0:
            # holders copy text
            new_page.saveState()
            new_page.rotate(90)
            new_page.setFont("Helvetica", 12)
            new_page.drawString(600, -85, "Holder's copy")
            new_page.restoreState()

        if page_total > 0 and page_number != page_total - 1:
            # Bottom of page horizontal line
            new_page.line(left_margin, 46, right_margin, 46)

        new_page.save()

        packet.seek(0)
        new_pdf = pypdf.PdfReader(packet)
        page.merge_page(new_pdf.pages[0])
        writer.add_page(page)

    with io.BytesIO() as bytes_stream:
        writer.write(bytes_stream)
        return bytes_stream.getvalue()
