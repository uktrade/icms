import datetime as dt

from django.urls import reverse

from .base import BaseResultsSerializer, BaseSerializer


class CaseDocumentSerializer(BaseSerializer):
    application_id: int
    issue_date: dt.datetime
    document_type: str
    reference: str | None

    # Export certificates only
    country: str | None

    # Import licences only
    issue_paper_licence_only: bool | None
    licence_start_date: dt.date | None
    licence_end_date: dt.date | None

    @staticmethod
    def url() -> str:
        return reverse("data-workspace:case-document-data", kwargs={"version": "v0"})


class CaseDocumentListSerializer(BaseResultsSerializer):
    results: list[CaseDocumentSerializer]


# TODO ECIL-630:
# VariationRequest
# CaseNote
# FIR
# UpdateRequest
# CaseEmail
