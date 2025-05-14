import datetime as dt

from .base import ApplicationBaseSerializer, BaseResultsSerializer
from .case import CaseDocumentSerializer


class ImportApplicationSerializer(ApplicationBaseSerializer):
    application_sub_type: str | None
    importer_id: int
    importer_office_id: int | None
    legacy_case_flag: bool | None
    chief_usage_status: str | None
    variation_decision: str | None
    variation_refuse_reason: str | None
    origin_country_name: str | None
    consignment_country_name: str | None
    commodity_group_id: int | None
    cover_letter_text: str | None
    imi_submitted_by_id: int | None
    imi_submit_datetime: dt.datetime | None


class ImportApplicationListSerializer(BaseResultsSerializer):
    results: list[ImportApplicationSerializer]


class ImportLicenceDocumentSerializer(CaseDocumentSerializer):
    issue_paper_licence_only: bool | None
    licence_start_date: dt.date | None
    licence_end_date: dt.date | None


class ImportLicenceDocumentListSerializer(BaseResultsSerializer):
    results: list[CaseDocumentSerializer]
