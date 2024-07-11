import base64
import io
from unittest import mock

import PIL
import pytest

from web.domains.signature import utils as signature_utils
from web.utils.pdf import utils as pdf_utils


@pytest.fixture()
def block_image():
    """Returns a dummy block image."""
    image = PIL.Image.new("RGBA", size=(50, 50), color=(256, 0, 0))
    image_file = io.BytesIO()
    image.save(image_file, "PNG")
    return image_file.getvalue()


@pytest.fixture(autouse=True)
def dummy_signature_image_base64(monkeypatch, block_image):
    """Patches the get_signature_file_base64() function to return a dummy signature image which actually has
    a width/height, so we can check formatting"""
    base64_str = base64.b64encode(block_image).decode("utf-8")  # /PS-IGNORE

    # get_signature_file_base64 has already been monkey-patched by the mock_signature_file fixture, so just need to
    # change the return value
    signature_utils.get_signature_file_base64.return_value = base64_str


@pytest.fixture(autouse=True)
def dummy_certificate_document_context(monkeypatch, block_image):
    """Patches the _certificate_document_context() function to return a dummy context.

    This context will always return the same QR code image and reference."""
    mock_get_certificate_context = mock.create_autospec(pdf_utils._certificate_document_context)
    mock_get_certificate_context.return_value = {
        "qr_check_url": "https://example.com",
        "certificate_code": "1234567",
        "qr_img_base64": base64.b64encode(block_image).decode("utf-8"),  # /PS-IGNORE
        "reference": "CFS/2024342/299929",
    }
    monkeypatch.setattr(pdf_utils, "_certificate_document_context", mock_get_certificate_context)
