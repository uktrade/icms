import http
from typing import Any, ClassVar

import pydantic
from django.contrib.auth.models import Group
from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import F, FilteredRelation, OuterRef, Q, QuerySet
from django.http import Http404, HttpRequest, JsonResponse
from django.views.generic import ListView, View

from web.models import (
    ExporterUserObjectPermission,
    ImporterUserObjectPermission,
    User,
    UserFeedbackSurvey,
)
from web.utils.api.auth import HawkAuthMixin

from . import serializers

VERSION = 0


class MetadataView(HawkAuthMixin, View):
    http_method_names = ["post"]

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        data = serializers.MetadataListSerializer(
            metadata=[serializer.get_metadata() for serializer in serializers.DATA_SERIALIZERS]
        ).model_dump(mode="json", exclude_defaults=True)
        return JsonResponse(data["metadata"], status=http.HTTPStatus.OK, safe=False)


class DataViewBase(HawkAuthMixin, ListView):
    http_method_names = ["post"]
    qs_serializer: ClassVar[type[serializers.BaseSerializer]]
    list_field: str
    data_serializer: ClassVar[type[serializers.BaseSerializer]]
    min_version: int = 0
    max_version: int = VERSION
    order_by: str = "pk"

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        version = self.kwargs["version"]
        self.version_number = int(version[1:])
        if self.version_number < self.min_version or self.version_number > self.max_version:
            raise Http404(
                f"This endpoint is only available from v{self.min_version} to v{self.max_version}"
            )

        data = self.get_data()
        return JsonResponse(data, status=http.HTTPStatus.OK, safe=False)

    def get_qs_serializer(self) -> type[pydantic.BaseModel]:
        """Returns the queryset serilaizer. Allows override of the queryset serializer for specific versions"""
        return self.qs_serializer

    def get_data_serializer(self) -> type[pydantic.BaseModel]:
        """Returns the data serializer. Allows override of the data serializer for specific versions"""
        return self.data_serializer

    def get_data(self) -> list[dict[str, Any]]:
        """Fetches the queryset and return a json dump of the data"""
        qs_serializer = self.get_qs_serializer()
        queryset = self.get_queryset()
        data = qs_serializer(**{self.list_field: list(queryset)}).model_dump(mode="json")
        return data[self.list_field]

    def get_queryset_annotations(self) -> dict[str, Any]:
        """Returns a dict of annotations to be used in get_queryset"""
        return {}

    def get_queryset_values(self) -> list[str]:
        """Returns a list of values to restrict the fields returned by get_queryset"""
        data_serializer = self.get_data_serializer()
        return list(data_serializer.model_fields.keys())

    def get_queryset_filters(self) -> dict[str, Any]:
        """Returns a dict of filters to be used in get_queryset"""
        return {}

    def get_queryset(self) -> QuerySet[Any]:
        """Returns the queryset"""
        qs = super().get_queryset()
        return (
            qs.filter(**self.get_queryset_filters())
            .annotate(**self.get_queryset_annotations())
            .order_by(self.order_by)
            .values(*self.get_queryset_values())
        )


class UserDataView(DataViewBase):
    # View Config
    model = User
    qs_serializer = serializers.Users
    data_serializer = serializers.UserSerializer
    list_field = "users"

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
    list_field = "surveys"
