from typing import Any

from django.db.models import Case, CharField, DateTimeField, F, IntegerField, When

from web.data_workspace import serializers
from web.models import CaseDocumentReference

from .base import DataViewBase


class CaseDocumentDataView(DataViewBase):
    model = CaseDocumentReference
    qs_serializer = serializers.CaseDocumentListSerializer
    data_serializer = serializers.CaseDocumentSerializer

    # TODO ECIL-629: Expand the filter to include active import app types
    def get_queryset_filters(self) -> dict[str, Any]:
        return {"export_application_certificates__isnull": False}

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return {
            "country": F("reference_data__country__name"),
            "issue_paper_licence_only": F("import_application_licences__issue_paper_licence_only"),
            "licence_start_date": F("import_application_licences__licence_start_date"),
            "licence_end_date": F("import_application_licences__licence_end_date"),
        }

    def get_queryset_annotations(self) -> dict[str, Any]:
        return {
            "issue_date": Case(
                When(
                    export_application_certificates__case_completion_datetime__isnull=True,
                    then="import_application_licences__case_completion_datetime",
                ),
                default="export_application_certificates__case_completion_datetime",
                output_field=DateTimeField(),
            ),
            "application_id": Case(
                When(
                    export_application_certificates__export_application_id__isnull=True,
                    then="import_application_licences__import_application_id",
                ),
                default="export_application_certificates__export_application_id",
                output_field=IntegerField(),
            ),
            "document_pack_id": Case(
                When(
                    export_application_certificates__id=True,
                    then="import_application_licences__id",
                ),
                default="export_application_certificates__id",
                output_field=IntegerField(),
            ),
            "document_pack_status": Case(
                When(
                    export_application_certificates__status__isnull=True,
                    then="import_application_licences__status",
                ),
                default="export_application_certificates__status",
                output_field=CharField(),
            ),
        }
