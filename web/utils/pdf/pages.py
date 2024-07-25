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


def format_firearm_licence_pages(
    pdf_data: bytes, context: dict[str, Any], left_margin: int = 36, right_margin: int = 574
) -> bytes:
    """Function to draw the top/bottom border lines on firearm licences"""
    reader = pypdf.PdfReader(io.BytesIO(pdf_data))
    writer = pypdf.PdfWriter()
    page_total = len(reader.pages)

    if page_total == 1:
        # don't bother with any borders if the entire licence is on 1 page
        return pdf_data

    signature_page_seen = False

    for page_number, page in enumerate(reader.pages):
        packet = io.BytesIO()
        new_page = canvas.Canvas(packet, pagesize=portrait(A4))

        if page_number >= 1 and not signature_page_seen:
            # add the top closing line to all pages except the first
            new_page.line(left_margin, 813, right_margin, 813)

        if f"Date Issued: {context['licence_start_date']}" in page.extract_text():
            # we're at the signature page, mark it as seen, so we don't add any more lines
            # as we know the box has already been closed with CSS
            signature_page_seen = True

        if page_total > 1 and page_number < page_total - 1 and not signature_page_seen:
            # if there is more than one page, add the bottom closing line unless it's the last page.
            # this is because the last page already has the bottom line in CSS
            new_page.line(left_margin, 31, right_margin, 31)

        new_page.save()
        packet.seek(0)
        new_pdf = pypdf.PdfReader(packet)

        if new_pdf.pages:
            page.merge_page(new_pdf.pages[0])

        writer.add_page(page)

    with io.BytesIO() as bytes_stream:
        writer.write(bytes_stream)
        return bytes_stream.getvalue()


def format_dfl_pages(pdf_data: bytes, context: dict[str, Any]) -> bytes:
    """Function to draw the top/bottom border lines on DFL licences"""
    return format_firearm_licence_pages(pdf_data, context)


def format_oil_pages(pdf_data: bytes, context: dict[str, Any]) -> bytes:
    """Function to draw the top/bottom border lines on OIL licences"""
    return format_firearm_licence_pages(pdf_data, context)


def format_sil_pages(pdf_data: bytes, context: dict[str, Any]) -> bytes:
    """Function to draw the top/bottom border lines on SIL licences"""
    return format_firearm_licence_pages(pdf_data, context)


def format_sanctions_pages(pdf_data: bytes, context: dict[str, Any]) -> bytes:
    start_date = context["licence_start_date"]

    reader = pypdf.PdfReader(io.BytesIO(pdf_data))
    writer = pypdf.PdfWriter()

    top_margin = 810
    left_margin = 53
    right_margin = 565
    page_total = len(reader.pages)
    for page_number, page in enumerate(reader.pages):
        packet = io.BytesIO()
        new_page = canvas.Canvas(packet, pagesize=portrait(A4))

        if page_number == 0:
            # Header
            new_page.setFont("Helvetica-Bold", 10)
            new_page.drawRightString(165, top_margin, "ELECTRONIC LICENCE")
            new_page.setFont("Helvetica", 10)
            new_page.drawRightString(
                455,
                top_margin,
                f"issued on {start_date} and sent to HM Revenue and Customs",
            )

            # Numbers in holders copy box
            new_page.setFontSize(14)
            new_page.drawRightString(left_margin - 8, 770, "1")
            new_page.drawRightString(left_margin - 8, 519, "1")

            # holders copy text
            new_page.saveState()
            new_page.rotate(90)
            new_page.setFontSize(12)
            new_page.drawString(610, -45, "Holder's copy")
            new_page.restoreState()

            # holders copy box
            new_page.setLineWidth(0.4)
            # holders copy box - vertical line
            new_page.line(left_margin - 25, 791, left_margin - 25, 499)
            # holders copy box - top box - horizontal line
            new_page.line(left_margin - 25, 791, left_margin, 791)
            # holders copy box - top box - bottom horizontal line
            new_page.line(left_margin - 25, 750, left_margin, 750)
            # holders copy box - bottom box - top horizontal line
            new_page.line(left_margin - 25, 539, left_margin, 539)
            # holders copy box - bottom box - bottom horizontal line
            new_page.line(left_margin - 25, 499, left_margin, 499)
        else:
            # On secondary pages - Lift top horizontal line a few pixels so the line does not crash into text
            new_page.setLineWidth(0.7)
            # Top Horizontal line across the full page
            new_page.line(left_margin, 794, right_margin, 794)
            # Small vertical line on left to extend border
            new_page.line(left_margin, 794, left_margin, 791)
            # Small vertical line on right to extend border
            new_page.line(right_margin, 794, right_margin, 791)

        if page_total > 0 and page_number != page_total - 1:
            # if more than one page add a horizontal line at the end of each page
            new_page.setLineWidth(0.7)
            new_page.line(left_margin, 45, right_margin, 45)

        new_page.save()

        packet.seek(0)
        new_pdf = pypdf.PdfReader(packet)
        page.merge_page(new_pdf.pages[0])
        writer.add_page(page)

    with io.BytesIO() as bytes_stream:
        writer.write(bytes_stream)
        return bytes_stream.getvalue()
