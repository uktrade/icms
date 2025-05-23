from typing import Any

from django.db.models import Case, Count, IntegerField, When

from web.data_workspace import serializers
from web.models import CaseNote, VariationRequest

from .base import DataViewBase


class CaseNoteDataView(DataViewBase):
    model = CaseNote
    qs_serializer = serializers.CaseNoteListSerializer
    data_serializer = serializers.CaseNoteSerializer

    def get_queryset_filters(self) -> dict[str, Any]:
        return {"is_active": True}

    def get_queryset_annotations(self) -> dict[str, Any]:
        return {
            "application_id": Case(
                When(
                    importapplication__id__isnull=False,
                    then="importapplication__id",
                ),
                default="exportapplication__id",
                output_field=IntegerField(),
            ),
            "file_count": Count("files"),
        }


class VariationRequestDataView(DataViewBase):
    model = VariationRequest
    qs_serializer = serializers.VariationRequestListSerializer
    data_serializer = serializers.VariationRequestSerializer

    def get_queryset_filters(self) -> dict[str, Any]:
        return {"is_active": True}

    def get_queryset_annotations(self) -> dict[str, Any]:
        return {
            "application_id": Case(
                When(
                    importapplication__id__isnull=False,
                    then="importapplication__id",
                ),
                default="exportapplication__id",
                output_field=IntegerField(),
            )
        }
