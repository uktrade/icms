from typing import Any

from django.db.models.query import QuerySet
from django.http import HttpRequest

from web.forms.widgets import ICMSModelSelect2Widget
from web.models import Commodity, Country, ImportApplicationType
from web.utils.commodity import (
    get_usage_commodities,
    get_usage_countries,
    get_usage_records,
)


class DerogationCountryOfOriginSelect(ICMSModelSelect2Widget):
    queryset = Country.objects.none()

    search_fields = ["name__icontains"]

    def get_queryset(self) -> "QuerySet[Country]":
        return get_usage_countries(ImportApplicationType.Types.DEROGATION)

    def build_attrs(
        self, base_attrs: dict[str, Any], extra_attrs: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        attrs = super().build_attrs(base_attrs, extra_attrs)

        attrs["data-minimum-input-length"] = 0
        attrs["data-placeholder"] = "Please choose a Country"

        return attrs


class DerogationCommoditySelect(ICMSModelSelect2Widget):
    queryset = Commodity.objects.none()

    # The value entered by the user is used to search the commodity code
    search_fields = ["commodity_code__contains"]

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {"origin_country": "origin_country"}

    def build_attrs(
        self, base_attrs: dict[str, Any], extra_attrs: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        attrs = super().build_attrs(base_attrs, extra_attrs)

        attrs["data-minimum-input-length"] = 0
        attrs["data-placeholder"] = "Please choose a Commodity"

        return attrs

    def get_queryset(self) -> "QuerySet[Commodity]":
        return get_usage_commodities(get_usage_records(ImportApplicationType.Types.DEROGATION))

    def filter_queryset(
        self,
        request: HttpRequest,
        term: str,
        queryset: QuerySet | None = None,
        **dependent_fields: Any,
    ) -> "QuerySet[Commodity]":
        """Filter the available Commodities depending on the origin country selected by the user."""

        if queryset is None:
            queryset = self.get_queryset()

        origin_country_pk: int | None = dependent_fields.get("origin_country")

        if not origin_country_pk:
            return queryset.none()

        country_of_origin = Country.objects.get(pk=origin_country_pk)

        usage_records = get_usage_records(ImportApplicationType.Types.DEROGATION).filter(
            country=country_of_origin
        )

        return get_usage_commodities(usage_records)
