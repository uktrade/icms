from typing import Any

from django.db.models import F

from web.data_workspace import serializers
from web.models import ImportApplication

from .base import ApplicationDataViewBase


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
