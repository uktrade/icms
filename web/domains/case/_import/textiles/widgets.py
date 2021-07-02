from typing import Optional

from django.db.models.query import QuerySet
from django.http import HttpRequest
from django_select2 import forms as s2forms

from web.domains.commodity.models import Commodity, CommodityGroup, Country


class TextilesCategoryCommodityGroupWidget(s2forms.ModelSelect2Widget):
    queryset = CommodityGroup.objects.filter(commodity_type__type_code="TEXTILES")

    # The value entered by the user is used to search the commodity code
    search_fields = ["group_code__contains"]

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {"origin_country": "origin_country"}

    def filter_queryset(
        self, request: HttpRequest, term: str, queryset: QuerySet = None, **dependent_fields
    ) -> QuerySet:
        """Filter the available categories depending on the origin country selected by the user."""

        if queryset is None:
            queryset = self.get_queryset()

        origin: Optional[str] = dependent_fields.get("origin_country")

        if not origin:
            return queryset.none()

        group_categories = self._get_group_categories()
        valid_groups = group_categories[int(origin)]

        return queryset.filter(group_code__in=valid_groups).order_by("pk")

    def _get_group_categories(self) -> dict[int, list[str]]:
        """Return the restricted list of categories for each available country."""

        return {
            Country.objects.get(name="Belarus").pk: [
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "15",
                "20",
                "21",
                "22",
                "24",
                "26",
                "27",
                "29",
                "67",
                "73",
                "115",
                "117",
                "118",
            ],
            Country.objects.get(name="Korea (North)").pk: [
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "12",
                "13",
                "14",
                "15",
                "16",
                "17",
                "18",
                "19",
                "20",
                "21",
                "22",
                "23",
                "24",
                "26",
                "27",
                "28",
                "29",
                "31",
                "32",
                "33",
                "34",
                "35",
                "36",
                "37",
                "39",
                "40",
                "41",
                "42",
                "49",
                "50",
                "53",
                "54",
                "55",
                "58",
                "59",
                "61",
                "62",
                "63",
                "65",
                "66",
                "67",
                "68",
                "69",
                "70",
                "72",
                "73",
                "74",
                "75",
                "76",
                "77",
                "78",
                "83",
                "84",
                "85",
                "86",
                "87",
                "88",
                "90",
                "91",
                "93",
                "97",
                "99",
                "100",
                "101",
                "109",
                "111",
                "112",
                "113",
                "114",
                "117",
                "118",
                "120",
                "121",
                "122",
                "123",
                "124",
                "133",
                "134",
                "135",
                "136",
                "137",
                "138",
                "140",
                "141",
                "142",
                "145",
                "149",
                "150",
                "153",
                "156",
                "157",
                "159",
                "160",
                "161",
                "130A",
                "130B",
                "146A",
                "146B",
                "146C",
                "151A",
                "151B",
                "38A",
                "38B",
            ],
        }


class TextilesCommodityWidget(s2forms.ModelSelect2Widget):
    queryset = Commodity.objects.filter(commoditygroup__commodity_type__type_code="TEXTILES")

    # The value entered by the user is used to search the commodity code
    search_fields = ["commodity_code__contains"]

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {"category_commodity_group": "commoditygroup__group_code"}

    def label_from_instance(self, commodity):
        return commodity.commodity_code
