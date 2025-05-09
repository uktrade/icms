from typing import Any

from django.contrib.auth.models import Group
from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import F, FilteredRelation, OuterRef, Q

from web.data_workspace import serializers
from web.models import (
    Exporter,
    ExporterUserObjectPermission,
    Importer,
    ImporterUserObjectPermission,
    Office,
    User,
    UserFeedbackSurvey,
)

from .base import DataViewBase


class UserDataView(DataViewBase):
    # View Config
    model = User
    qs_serializer = serializers.UserListSerializer
    data_serializer = serializers.UserSerializer

    def get_queryset_annotations(self) -> dict[str, Any]:
        return {
            "group_names": ArraySubquery(
                Group.objects.filter(user__pk=OuterRef("pk"))
                .values_list("name", flat=True)
                .distinct()
            ),
            "exporter_ids": ArraySubquery(
                ExporterUserObjectPermission.objects.filter(user__pk=OuterRef("pk"))
                .values_list("content_object_id", flat=True)
                .distinct()
            ),
            "importer_ids": ArraySubquery(
                ImporterUserObjectPermission.objects.filter(user__pk=OuterRef("pk"))
                .values_list("content_object_id", flat=True)
                .distinct()
            ),
            "primary_email": FilteredRelation("emails", condition=Q(emails__is_primary=True)),
            "primary_email_address": F("primary_email__email"),
        }

    def get_queryset_filters(self) -> dict[str, Any]:
        return {"pk__gt": 0}


class UserFeedbackSurveyDataView(DataViewBase):
    model = UserFeedbackSurvey
    qs_serializer = serializers.UserFeedbackSurveys
    data_serializer = serializers.UserFeedbackSurveySerializer

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return {"application_id": F("process_id")}


class ImporterDataView(DataViewBase):
    model = Importer
    qs_serializer = serializers.ImporterListSerializer
    data_serializer = serializers.ImporterSerializer


class ExporterDataView(DataViewBase):
    model = Exporter
    qs_serializer = serializers.ExporterListSerializer
    data_serializer = serializers.ExporterSerializer


class OfficeDataView(DataViewBase):
    model = Office
    qs_serializer = serializers.OfficeListSerializer
    data_serializer = serializers.OfficeSerializer

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return {"importer_id": F("importer__id"), "exporter_id": F("exporter__id")}
