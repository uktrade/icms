import base64

from web.domains.case.services import document_pack
from web.models import CaseDocumentReference, File
from web.utils.s3 import get_file_from_s3, get_s3_client


def _get_gov_notify_attachment_data(contents) -> dict:
    return {
        "file": base64.b64encode(contents).decode("ascii"),  # /PS-IGNORE
        "is_csv": False,
        "confirm_email_before_download": None,
        "retention_period": "1 week",
    }


def _get_file_contents(case_document_reference: CaseDocumentReference) -> bytes | None:
    _file = (
        File.objects.filter(pk=case_document_reference.document_id)
        .values("path", "filename")
        .order_by("pk")
        .last()
    )
    if not _file:
        return None
    s3_client = get_s3_client()
    return get_file_from_s3(_file["path"], client=s3_client)


def get_attachment_data(application, document_type) -> dict:
    """
    TODO: ICMSLST-2333 Gov Notify - Email attachments

    If its decided that that attachments are going to be sent within emails.
    Add a function similar to the one below to each relevant Email Message and add to the email context

    def add_attachments(self):
        return {
            'licence_attachment': get_attachment_data(self.application, CaseDocumentReference.Type.LICENCE),
            'cover_letter_attachment': get_attachment_data(self.application, CaseDocumentReference.Type.COVER_LETTER)
        }
    """
    doc_pack = document_pack.pack_active_get(application)
    document = doc_pack.document_references.filter(document_type=document_type).last()
    if not document:
        return {}
    file_contents = _get_file_contents(document)
    if file_contents:
        return _get_gov_notify_attachment_data(file_contents)
    return {}
