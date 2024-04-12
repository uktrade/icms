from typing import Any

from django.db.models.query import QuerySet
from django.http import HttpRequest
from django_select2 import forms as s2forms

from web.models import Commodity, CommodityGroup, Country, ImportApplicationType
from web.utils.commodity import get_usage_commodities, get_usage_records


class IronSteelCommodityGroupSelect(s2forms.ModelSelect2Widget):
    queryset = CommodityGroup.objects.filter(commodity_type__type_code="IRON_STEEL")

    # The value entered by the user is used to search the commodity code
    search_fields = ["group_code__icontains"]

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {"origin_country": "origin_country"}

    def build_attrs(
        self, base_attrs: dict[str, Any], extra_attrs: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        attrs = super().build_attrs(base_attrs, extra_attrs)

        attrs["data-minimum-input-length"] = 0
        attrs["data-placeholder"] = "Please choose a Category"

        return attrs

    def filter_queryset(
        self,
        request: HttpRequest,
        term: str,
        queryset: QuerySet | None = None,
        **dependent_fields: Any,
    ) -> QuerySet:
        """Filter the available categories depending on the origin country selected by the user."""

        if queryset is None:
            queryset = self.get_queryset()

        origin_country: str | None = dependent_fields.get("origin_country")

        if not origin_country:
            return queryset.none()

        usage_records = get_usage_records(ImportApplicationType.Types.IRON_STEEL).filter(
            country=origin_country
        )

        return queryset.filter(usages__in=usage_records).order_by("pk")


class IronSteelCommoditySelect(s2forms.ModelSelect2Widget):
    queryset = Commodity.objects.none()

    # The value entered by the user is used to search the commodity code
    search_fields = ["commodity_code__contains"]

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {
        "origin_country": "origin_country",
        "category_commodity_group": "commodity_group",
    }

    def build_attrs(
        self, base_attrs: dict[str, Any], extra_attrs: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        attrs = super().build_attrs(base_attrs, extra_attrs)

        attrs["data-minimum-input-length"] = 0
        attrs["data-placeholder"] = "Please choose a Commodity"

        return attrs

    def filter_queryset(
        self,
        request: HttpRequest,
        term: str,
        queryset: QuerySet | None = None,
        **dependent_fields: Any,
    ) -> "QuerySet[Commodity]":
        """Filter the available categories depending on the origin country selected by the user."""

        if queryset is None:
            queryset = self.get_queryset()

        origin_country: str | None = dependent_fields.get("origin_country")

        if not origin_country:
            return queryset.none()

        commodity_group: str | None = dependent_fields.get("commodity_group")

        if not commodity_group:
            return queryset.none()

        country_of_origin = Country.objects.get(pk=origin_country)

        usage_records = get_usage_records(ImportApplicationType.Types.IRON_STEEL).filter(
            country=country_of_origin
        )

        return get_usage_commodities(usage_records)
