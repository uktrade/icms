import base64
import datetime as dt
import io
import logging

import fitz
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from django.conf import settings
from endesive.pdf import cms
from PIL import Image

from web.domains.signature.utils import get_active_signature, get_signature_file_bytes
from web.utils.pdf.exceptions import SignatureTextNotFound

logger = logging.getLogger(__name__)


def get_active_signature_image() -> Image.Image:
    """Fetch the active signature image from s3 and return as a PIL Image object

    :return: PIL Image object
    """
    active_signature = get_active_signature()
    active_signature_bytes = get_signature_file_bytes(active_signature)
    return Image.open(io.BytesIO(active_signature_bytes))


def get_signature_coordinates(
    pdf_file: fitz.Document,
    signature_header_text: str = "Signed by",
    signature_footer_text: str = "On behalf of the Secretary of State",
) -> tuple[tuple[float, float, float, float], int]:
    """Searches a pdf file for the signature text and returns the coordinates of where signature image should be.

    These coordinates are use the bottom left corner as 0,0

    :param pdf_file: A fitz.Document object
    :param signature_header_text: The text that should appear before the signature image
    :param signature_footer_text: The text that should appear after the signature image
    :return:
    tuple - A tuple of floats representing the coordinates of the signature box
    integer - The page number the signature box is on
    """

    # we need to find where to place the signature on the pdf, we do this by searching for
    # the text before and after where the signature should go on the page
    # known as the signature_header and signature_footer respectively
    for page in pdf_file.pages():
        header_found = page.search_for(signature_header_text)
        footer_found = page.search_for(signature_footer_text)

        if header_found and footer_found:
            signature_header_text_rect = header_found[0]
            signature_footer_text_rect = footer_found[0]

            # Because PyMuPDF uses a different coordinate system to endesive we need to convert between the two
            # PyMuPDF uses the top left corner as 0,0 and endesive uses the bottom left corner as 0,0
            page_size = page.bound()
            signature_image_coordinates = (
                # we add and subtract 5 for the top-left and top-bottom
                # to give a little bit of padding around the signature image and ensure there is no overlap
                signature_footer_text_rect.x0 - 5,
                page_size.y1 - signature_footer_text_rect.y0,
                signature_footer_text_rect.x1 + 5,
                page_size.y1 - signature_header_text_rect.y1,
            )
            return signature_image_coordinates, page.number

    raise SignatureTextNotFound("Unable to find signature text in pdf")


def sign_pdf(target: io.BytesIO) -> io.BytesIO:
    """Takes a pdf written to a BytesIO stream and adds a digital signature."""

    pdf_bytes = target.getvalue()

    if not settings.P12_SIGNATURE_BASE_64:
        logger.info("P12_SIGNATURE_BASE_64 environment variable not set for this environment.")
        return target

    if not settings.P12_SIGNATURE_PASSWORD:
        logger.info("P12_SIGNATURE_PASSWORD environment variable not set for this environment.")
        return target

    # load the base64 encoded p12 certificate into memory
    loaded_p12_certificate = pkcs12.load_key_and_certificates(
        base64.b64decode(settings.P12_SIGNATURE_BASE_64),  # /PS-IGNORE
        password=settings.P12_SIGNATURE_PASSWORD.encode(),
        backend=backends.default_backend(),
    )

    pdf_file = fitz.open("pdf", pdf_bytes)
    signature_image_coordinates, page_number = get_signature_coordinates(pdf_file)

    # Now we need to load the active signature image from s3, and convert it to a PIL image object
    active_signature_image = get_active_signature_image()

    # Setting up signature metadata
    dct = {
        # aligned is the number of hexbytes in the PDF to reserve for the signature
        # aligned=0 tells endesive to precompute the size of the signature file so this is dynamic
        "aligned": 0,
        "sigpage": page_number,
        "auto_sigfield": True,
        "signaturebox": signature_image_coordinates,
        "signature_img": active_signature_image,
        "contact": "contact:enquiries.ilb@trade.gov.uk",  # /PS-IGNORE
        "location": "Department for Business and Trade",
        "signingdate": dt.datetime.utcnow().strftime("D:%Y%m%d%H%M%S+00'00'"),
        "reason": "On behalf of the Secretary of State",
    }

    # Now we can sign the pdf...Finally.
    pdf_signature = cms.sign(
        pdf_bytes,
        dct,
        loaded_p12_certificate[0],
        loaded_p12_certificate[1],
        loaded_p12_certificate[2],
        "sha256",
    )

    # Now we need to write the signed pdf to a BytesIO stream and return it
    signed_pdf = io.BytesIO()
    signed_pdf.write(pdf_bytes)
    signed_pdf.write(pdf_signature)
    return signed_pdf
