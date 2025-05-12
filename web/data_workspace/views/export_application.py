from typing import Any

from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import Exists, F, OuterRef, Value

from web.data_workspace import serializers
from web.models import (
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    CFSProduct,
    CFSProductActiveIngredient,
    CFSProductType,
    CFSSchedule,
    ExportApplication,
    ProductLegislation,
)

from .base import ApplicationDataViewBase, DataViewBase


class ExportApplicationDataView(ApplicationDataViewBase):
    model = ExportApplication
    qs_serializer = serializers.ExportApplicationListSerializer
    data_serializer = serializers.ExportApplicationSerializer

    def get_queryset_annotations(self) -> dict[str, Any]:
        return super().get_queryset_annotations() | {
            "country_names": ArrayAgg(
                "countries__name",
                distinct=True,
                default=Value([]),
            )
        }

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return super().get_queryset_value_kwargs() | {
            "application_type_code": F("application_type__type_code")
        }


class GMPApplicationDataView(DataViewBase):
    model = CertificateOfGoodManufacturingPracticeApplication
    qs_serializer = serializers.GMPApplicationListSerializer
    data_serializer = serializers.GMPApplicationSerializer

    def get_queryset_annotations(self) -> dict[str, Any]:
        return {
            "supporting_documents_types": ArrayAgg(
                "supporting_documents__file_type",
                distinct=True,
                default=Value([]),
            )
        }


class COMApplicationDataView(DataViewBase):
    model = CertificateOfManufactureApplication
    qs_serializer = serializers.COMApplicationListSerializer
    data_serializer = serializers.COMApplicationSerializer


class CFSScheduleDataView(DataViewBase):
    model = CFSSchedule
    qs_serializer = serializers.CFSScheduleListSerializer
    data_serializer = serializers.CFSScheduleSerializer

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return {
            "export_application_id": F("application_id"),
            "country_of_manufacture_name": F("country_of_manufacture__name"),
        }

    def get_queryset_annotations(self) -> dict[str, Any]:
        return {
            "legislation_ids": ArrayAgg(
                "legislations__pk",
                distinct=True,
                default=Value([]),
            ),
            "is_biocidal": Exists(
                ProductLegislation.objects.filter(is_biocidal=True, cfsschedule=OuterRef("pk")),
            ),
            "is_biocidal_claim": Exists(
                ProductLegislation.objects.filter(
                    is_biocidal_claim=True, cfsschedule=OuterRef("pk")
                ),
            ),
        }


class CFSProductDataView(DataViewBase):
    model = CFSProduct
    qs_serializer = serializers.CFSProductListSerializer
    data_serializer = serializers.CFSProductSerializer

    def get_queryset_annotations(self) -> dict[str, Any]:
        return {
            "product_type_number_list": ArraySubquery(
                CFSProductType.objects.filter(product_id=OuterRef("pk"))
                .values_list("product_type_number", flat=True)
                .distinct()
            ),
            "active_ingredient_list": ArraySubquery(
                CFSProductActiveIngredient.objects.filter(product_id=OuterRef("pk"))
                .values_list("name", flat=True)
                .order_by("pk")
            ),
            "cas_number_list": ArraySubquery(
                CFSProductActiveIngredient.objects.filter(product_id=OuterRef("pk"))
                .values_list("cas_number", flat=True)
                .order_by("pk")
            ),
        }


class LegislationDataView(DataViewBase):
    model = ProductLegislation
    qs_serializer = serializers.LegislationListSerializer
    data_serializer = serializers.LegislationSerializer
