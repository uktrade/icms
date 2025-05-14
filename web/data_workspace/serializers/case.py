import datetime as dt

from .base import BaseSerializer


class CaseDocumentSerializer(BaseSerializer):
    application_id: int
    document_pack_id: int
    document_pack_status: str
    issue_date: dt.datetime | None
    document_type: str
    reference: str | None


# TODO ECIL-630:
# VariationRequest
# CaseNote
# FIR
# UpdateRequest
# CaseEmail
