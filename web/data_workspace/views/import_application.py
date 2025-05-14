from typing import Any

from django.db.models import F

from web.data_workspace import serializers
from web.models import CaseDocumentReference, ImportApplication

from .base import ApplicationDataViewBase, DataViewBase


class ImportApplicationDataView(ApplicationDataViewBase):
    model = ImportApplication
    qs_serializer = serializers.ImportApplicationListSerializer
    data_serializer = serializers.ImportApplicationSerializer

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return super().get_queryset_value_kwargs() | {
            "application_type_code": F("application_type__type"),
            "application_sub_type": F("application_type__sub_type"),
            "origin_country_name": F("origin_country__name"),
            "consignment_country_name": F("consignment_country__name"),
        }


class ImportLicenceDocumentDataView(DataViewBase):
    model = CaseDocumentReference
    qs_serializer = serializers.ImportLicenceDocumentListSerializer
    data_serializer = serializers.ImportLicenceDocumentSerializer

    def get_queryset_filters(self) -> dict[str, Any]:
        return {
            "import_application_licences__import_application__application_type__is_active": True
        }

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return {
            "application_id": F("import_application_licences__import_application_id"),
            "document_pack_id": F("import_application_licences__id"),
            "document_pack_status": F("import_application_licences__status"),
            "issue_date": F("import_application_licences__case_completion_datetime"),
            "issue_paper_licence_only": F("import_application_licences__issue_paper_licence_only"),
            "licence_start_date": F("import_application_licences__licence_start_date"),
            "licence_end_date": F("import_application_licences__licence_end_date"),
        }
