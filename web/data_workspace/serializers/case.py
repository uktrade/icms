import datetime as dt

from .base import BaseResultsSerializer, BaseSerializer


class CaseDocumentSerializer(BaseSerializer):
    application_id: int
    document_pack_id: int
    document_pack_status: str
    issue_date: dt.datetime | None
    document_type: str
    reference: str | None


class CaseNoteSerializer(BaseSerializer):
    application_id: int
    note: str | None
    file_count: int
    create_datetime: dt.datetime
    created_by_id: int
    updated_at: dt.datetime
    updated_by_id: int | None


class CaseNoteListSerializer(BaseResultsSerializer):
    results: list[CaseNoteSerializer]


class UpdateRequestSerializer(BaseSerializer):
    application_id: int
    request_subject: str | None
    request_detail: str | None
    response_detail: str | None
    request_datetime: dt.datetime | None
    requested_by_id: int | None
    response_datetime: dt.datetime | None
    response_by_id: int | None
    closed_datetime: dt.datetime | None
    closed_by_id: int | None


class UpdateRequestListSerializer(BaseResultsSerializer):
    results: list[UpdateRequestSerializer]


class VariationRequestSerializer(BaseSerializer):
    application_id: int
    status: str
    extension_flag: bool
    requested_datetime: dt.datetime
    requested_by_id: int
    what_varied: str
    why_varied: str | None
    when_varied: dt.date | None
    reject_cancellation_reason: str | None
    update_request_reason: str | None
    closed_datetime: dt.datetime | None
    closed_by_id: int | None


class VariationRequestListSerializer(BaseResultsSerializer):
    results: list[VariationRequestSerializer]


# TODO ECIL-630:
# FIR
# CaseEmail
