from typing import Any

from django.db.models.query import QuerySet
from django.http import HttpRequest

from web.forms.widgets import ICMSModelSelect2Widget
from web.models import Commodity, CommodityGroup, Country, ImportApplicationType
from web.utils.commodity import get_usage_commodity_groups, get_usage_records
from web.utils.sort import sort_integer_strings


class TextilesCategoryCommodityGroupWidget(ICMSModelSelect2Widget):
    queryset = CommodityGroup.objects.filter(commodity_type__type_code="TEXTILES")

    # The value entered by the user is used to search the commodity code
    search_fields = ["group_code__icontains"]

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {"origin_country": "origin_country"}

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

        origin: str | None = dependent_fields.get("origin_country")

        if not origin:
            return queryset.none()

        country_of_origin = Country.objects.get(pk=origin)

        usage_records = get_usage_records(ImportApplicationType.Types.TEXTILES).filter(
            country=country_of_origin
        )

        commodity_groups = get_usage_commodity_groups(usage_records)

        return sort_integer_strings(commodity_groups, "group_code")


class TextilesCommodityWidget(ICMSModelSelect2Widget):
    queryset = Commodity.objects.filter(commoditygroup__commodity_type__type_code="TEXTILES")

    # The value entered by the user is used to search the commodity code
    search_fields = ["commodity_code__contains"]

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {"category_commodity_group": "commoditygroup__group_code"}

    def label_from_instance(self, commodity):
        return commodity.commodity_code
