import http
from typing import Any, ClassVar

import pydantic
from django.db.models import QuerySet
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.views.generic import ListView, View

from web.data_workspace import serializers
from web.utils.api.auth import HawkDataWorkspaceMixin

VERSION = 0


class MetadataView(HawkDataWorkspaceMixin, View):
    http_method_names = ["get"]

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        data = serializers.MetadataListSerializer(
            tables=[serializer.get_metadata() for serializer in serializers.DATA_SERIALIZERS]
        ).model_dump(mode="json", exclude_defaults=True)
        return JsonResponse(data, status=http.HTTPStatus.OK)


class DataViewBase(HawkDataWorkspaceMixin, ListView):
    http_method_names = ["get"]
    qs_serializer: ClassVar[type[serializers.BaseResultsSerializer]]
    data_serializer: ClassVar[type[serializers.BaseSerializer]]
    min_version: int = 0
    max_version: int = VERSION
    order_by: str = "pk"
    paginate_by = 1000

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        version = self.kwargs["version"]
        self.version_number = int(version[1:])
        if self.version_number < self.min_version or self.version_number > self.max_version:
            raise Http404(
                f"This endpoint is only available from v{self.min_version} to v{self.max_version}"
            )
        return super().dispatch(request, *args, **kwargs)

    def render_to_response(self, context: dict[str, Any], **response_kwargs: Any) -> HttpResponse:
        queryset = context["object_list"]
        data: dict[str, Any] = {"results": list(queryset)}

        paginator = context["paginator"]
        page = context["page_obj"]
        if page.number < paginator.num_pages:
            data["next"] = f"{self.request.path}?page={page.number + 1}"
        else:
            data["next"] = ""

        qs_serializer = self.get_qs_serializer()
        data = qs_serializer(**data).model_dump(mode="json", exclude_defaults=True)

        return JsonResponse(data, status=http.HTTPStatus.OK)

    def get_qs_serializer(self) -> type[pydantic.BaseModel]:
        """Returns the queryset serilaizer. Allows override of the queryset serializer for specific versions"""
        return self.qs_serializer

    def get_data_serializer(self) -> type[pydantic.BaseModel]:
        """Returns the data serializer. Allows override of the data serializer for specific versions"""
        return self.data_serializer

    def get_data(self) -> dict[str, Any]:
        """Fetches the queryset and return a json dump of the data"""
        qs_serializer = self.get_qs_serializer()
        queryset = self.get_queryset()
        return qs_serializer(**{self.list_field: list(queryset)}).model_dump(mode="json")

    def get_queryset_annotations(self) -> dict[str, Any]:
        """Returns a dict of annotations to be used in get_queryset"""
        return {}

    def get_queryset_values(self) -> list[str]:
        """Returns a list of values to restrict the fields returned by get_queryset"""
        data_serializer = self.get_data_serializer()
        return list(data_serializer.model_fields.keys())

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        """Returns a dict of values to restrict the fields returned by get_queryset"""
        return {}

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
            .values(*self.get_queryset_values(), **self.get_queryset_value_kwargs())
        )
