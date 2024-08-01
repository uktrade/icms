import base64
import io
from unittest import mock

import PIL
import pytest

from web.domains.case._import.models import EndorsementImportApplication
from web.domains.case.services import document_pack
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


@pytest.fixture(autouse=True)
def configure_settings(settings):
    """Manually fixes some settings that are inserted into the PDFs so that there is consistency between
    the benchmark and generated PDFs."""
    settings.ICMS_SANCTIONS_EMAIL = "sanctions@example.com"  # /PS-IGNORE
    settings.ILB_CONTACT_EMAIL = "contact@example.com"  # /PS-IGNORE
    settings.ILB_CONTACT_ADDRESS = "Import Licencing Branch, Queensway House, West Precinct, Billingham, TS23 2NF"  # /PS-IGNORE


@pytest.fixture
def pdf_long_oil_app(completed_oil_app):
    EndorsementImportApplication.objects.create(
        import_application=completed_oil_app, content="This is an endorsement" * 100
    )
    return completed_oil_app


@pytest.fixture
def pdf_paper_licence_only_oil_app(completed_oil_app):
    licence = document_pack.pack_active_get(completed_oil_app)
    licence.issue_paper_licence_only = True
    licence.save()
    return completed_oil_app


@pytest.fixture
def pdf_long_sil_app(completed_sil_app):
    EndorsementImportApplication.objects.create(
        import_application=completed_sil_app, content="This is an endorsement" * 100
    )
    return completed_sil_app


@pytest.fixture
def pdf_paper_licence_only_sil_app(completed_sil_app):
    licence = document_pack.pack_active_get(completed_sil_app)
    licence.issue_paper_licence_only = True
    licence.save()
    return completed_sil_app


@pytest.fixture
def pdf_long_dfl_app(completed_dfl_app):
    EndorsementImportApplication.objects.create(
        import_application=completed_dfl_app, content="This is an endorsement" * 100
    )
    return completed_dfl_app


@pytest.fixture
def pdf_paper_licence_only_dfl_app(completed_dfl_app):
    licence = document_pack.pack_active_get(completed_dfl_app)
    licence.issue_paper_licence_only = True
    licence.save()
    return completed_dfl_app


@pytest.fixture
def pdf_long_sanctions_app(completed_sanctions_app):
    EndorsementImportApplication.objects.create(
        import_application=completed_sanctions_app, content="This is an endorsement" * 100
    )
    return completed_sanctions_app


@pytest.fixture
def pdf_long_com_app(completed_com_app):
    completed_com_app.manufacturing_process = "This is a long manufacturing process" * 100
    completed_com_app.save()
    return completed_com_app


@pytest.fixture
def pdf_dfl_cover_letter_app(completed_dfl_app):
    completed_dfl_app.cover_letter_text = "Hello\n" * 10
    completed_dfl_app.save()
    return completed_dfl_app


@pytest.fixture
def pdf_long_dfl_cover_letter_app(completed_dfl_app):
    completed_dfl_app.cover_letter_text = "Hello\n" * 3000
    completed_dfl_app.save()
    return completed_dfl_app
