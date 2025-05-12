import datetime as dt

from .base import BaseResultsSerializer, BaseSerializer


class CaseDocumentSerializer(BaseSerializer):
    application_id: int
    document_pack_id: int
    document_pack_status: str
    issue_date: dt.datetime | None
    document_type: str
    reference: str | None

    # Export certificates only
    country: str | None

    # Import licences only
    issue_paper_licence_only: bool | None
    licence_start_date: dt.date | None
    licence_end_date: dt.date | None


class CaseDocumentListSerializer(BaseResultsSerializer):
    results: list[CaseDocumentSerializer]


# TODO ECIL-630:
# VariationRequest
# CaseNote
# FIR
# UpdateRequest
# CaseEmail
