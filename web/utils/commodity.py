from collections import defaultdict
from typing import TYPE_CHECKING, TypedDict

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import F, Model, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from web.models import Commodity, CommodityGroup, Country, Unit, Usage

if TYPE_CHECKING:
    from django.db.models import QuerySet


class CommodityGroupData(TypedDict):
    unit_description: str
    group_commodities: list[int]


def get_usage_records(app_type: str, app_sub_type: str | None = None) -> "QuerySet[Usage]":
    """Gets all Usage records for the supplied application type / subtype"""

    usage_records = Usage.objects.all()
    usage_records = add_usage_filter(usage_records, app_type, app_sub_type)

    return usage_records.distinct()


def add_usage_filter(
    model: "QuerySet[Model]", app_type: str, app_sub_type: str | None = None, usage_path: str = ""
) -> "QuerySet[Model]":
    """Apply all required filters to filter usage records correctly.

    :param model: The model to apply usage filters too.
    :param app_type: Type of application.
    :param app_sub_type: Optional subtype of application.
    :param usage_path: The path indicating the relationship to the usage model.
    """

    application_type_filters = {f"{usage_path}application_type__type": app_type}
    if app_sub_type:
        application_type_filters[f"{usage_path}application_type__subtype"] = app_sub_type

    today = timezone.now().date()

    return (
        model.filter(
            **{
                f"{usage_path}start_date__lte": today,
                f"{usage_path}commodity_group__commodities__validity_start_date__lte": today,
                f"{usage_path}commodity_group__is_active": True,
                f"{usage_path}commodity_group__commodities__is_active": True,
            },
            **application_type_filters,
        )
        .annotate(
            # Optional end dates need a default when checking
            usage_end_date=Coalesce(f"{usage_path}end_date", today),
            commodity_end_data=Coalesce(
                f"{usage_path}commodity_group__commodities__validity_end_date", today
            ),
        )
        .filter(
            usage_end_date__gte=today,
            commodity_end_data__gte=today,
        )
    )


def get_usage_countries(app_type: str, app_sub_type: str | None = None) -> "QuerySet[Country]":
    """Return countries linked to the usage records."""
    countries = Country.objects.filter(is_active=True)
    countries = add_usage_filter(countries, app_type, app_sub_type, "usage__")

    return countries.distinct()


def get_usage_commodity_groups(application_usage: "QuerySet[Usage]") -> "QuerySet[CommodityGroup]":
    """Return commodity groups linked to the usage records"""
    return CommodityGroup.objects.filter(usages__in=application_usage, is_active=True).distinct()


def get_usage_commodities(application_usage: "QuerySet[Usage]") -> "QuerySet[Commodity]":
    """Return commodities linked to the usage records."""
    groups = get_usage_commodity_groups(application_usage)

    return Commodity.objects.filter(commoditygroup__in=groups, is_active=True).distinct()


def annotate_commodity_unit(
    model: "QuerySet[Model]", commodity_path: str = ""
) -> "QuerySet[Model]":
    """Annotate a queryset with a unit_description.

    :param model: A model linked to commodities
    :param commodity_path: The path indicating the relationship to the commodity model.
    :return: annotated model
    """

    commodity_unit = Unit.objects.filter(
        pk=OuterRef(f"{commodity_path}commoditygroup__unit")
    ).order_by("-pk")

    return model.annotate(
        unit_description=Subquery(commodity_unit.values("description")[:1]),
        hmrc_code=Subquery(commodity_unit.values("hmrc_code")[:1]),
    )


def get_commodity_group_data(
    application_usage: "QuerySet[Usage]",
) -> dict[int, CommodityGroupData]:
    """Returns group data, specifically the linked commodities and the unit description"""
    groups = (
        get_usage_commodity_groups(application_usage)
        .annotate(group_commodities=ArrayAgg("commodities__pk", distinct=True, default=Value([])))
        .order_by("group_name")
    )

    return {
        g.pk: {"unit_description": g.unit.description, "group_commodities": g.group_commodities}
        for g in groups
    }


def get_commodity_unit(
    commodity_group_data: dict[int, CommodityGroupData], commodity: Commodity
) -> str:
    """Return the commodity unit by searching the commodity group data."""
    for group_id, group_data in commodity_group_data.items():
        if commodity.pk in group_data["group_commodities"]:
            return group_data["unit_description"]

    return ""


def get_category_commodity_group_data(commodity_type: str) -> dict[str, dict[str, str]]:
    groups = CommodityGroup.objects.filter(
        commodity_type__type_code=commodity_type,
    ).select_related("unit")

    group_data = {}
    for cg in groups:
        if cg.unit:
            unit_desc = cg.unit.description
        else:
            unit_desc = None

        group_data.update({cg.pk: {"label": cg.group_description, "unit": unit_desc}})

    return group_data


def get_active_commodities(commodities: "QuerySet[Commodity]") -> "QuerySet[Commodity]":
    """Filter commodities by date and active status"""
    today = timezone.now().date()

    return commodities.annotate(
        commodity_start_date=F("validity_start_date"),
        commodity_end_date=Coalesce("validity_end_date", today),
    ).filter(
        commodity_start_date__lte=today,
        commodity_end_date__gte=today,
        is_active=True,
    )


def get_usage_data(app_type: str, app_sub_type: str | None = None) -> dict[str, dict[str, float]]:
    usages = (
        get_usage_records(app_type, app_sub_type)
        .exclude(maximum_allocation__isnull=True)
        .values_list("commodity_group_id", "country_id", "maximum_allocation", named=True)
    )
    usage_data: dict[str, dict[str, float]] = defaultdict(dict)
    for u in usages:
        usage_data[u.commodity_group_id][u.country_id] = u.maximum_allocation

    return usage_data
