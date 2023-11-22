import base64
import io
import logging
import tempfile

from django.conf import settings
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers

logger = logging.getLogger(__name__)


def sign_pdf(target: io.BytesIO) -> io.BytesIO:
    """Takes a pdf written to a BytesIO stream and adds a digital signature."""

    if not settings.DIGITAL_SIGN_FLAG:
        logger.info("DIGITAL_SIGN_FLAG set to False for this environment.")
        return target

    if not settings.SIGNING_CERTIFICATE_PKCS12:
        logger.info("SIGNING_CERTIFICATE_PKS12 not set for this environment.")
        return target

    with tempfile.NamedTemporaryFile(suffix=".p12") as p12:
        pks12_string = settings.SIGNING_CERTIFICATE_PKCS12
        p12.write(base64.b64decode(pks12_string))  # /PS-IGNORE
        signer = signers.SimpleSigner.load_pkcs12(p12.name)  # type: ignore[no-untyped-call]

    writer = IncrementalPdfFileWriter(target)

    return signers.sign_pdf(
        writer,
        signers.PdfSignatureMetadata(
            field_name="Signature1",
            md_algorithm="sha256",
            location="Department for Business and Trade",
            reason="On behalf of the Secretary of State",
        ),
        signer=signer,
    )
