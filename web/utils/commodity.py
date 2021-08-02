from typing import TYPE_CHECKING

from django.db.models import F
from django.db.models.functions import Coalesce
from django.utils import timezone

from web.domains.case._import.models import ImportApplicationType
from web.domains.commodity.models import Commodity, CommodityGroup, Usage
from web.domains.country.models import Country

if TYPE_CHECKING:
    from django.db.models import QuerySet


def get_usage_records(app_type: str, app_sub_type: str = None) -> "QuerySet[Usage]":
    """Gets all Usage records for the supplied application type / subtype"""

    filter_kwargs = app_sub_type and {"subtype": app_sub_type} or {}
    application_type = ImportApplicationType.objects.get(type=app_type, **filter_kwargs)
    today = timezone.now().date()

    application_usage = (
        Usage.objects.annotate(
            usage_start_date=F("start_date"),
            commodity_start_date=F("commodity_group__commodities__validity_start_date"),
            # Optional end dates need a default when checking
            usage_end_date=Coalesce("end_date", today),
            commodity_end_data=Coalesce("commodity_group__commodities__validity_end_date", today),
        ).filter(
            application_type=application_type,
            usage_start_date__lte=today,
            usage_end_date__gte=today,
            commodity_start_date__lte=today,
            commodity_end_data__gte=today,
            commodity_group__is_active=True,
            commodity_group__commodities__is_active=True,
        )
        # Filtering the manytomany commodities causes duplicate records
        .distinct()
    )

    return application_usage


def get_usage_countries(application_usage: "QuerySet[Usage]") -> "QuerySet[Country]":
    """Return countries linked to the usage records."""
    return Country.objects.filter(usage__in=application_usage, is_active=True).distinct()


def get_usage_commodities(application_usage: "QuerySet[Usage]") -> "QuerySet[Commodity]":
    """Return commodities linked to the usage records."""
    return Commodity.objects.filter(
        commoditygroup__in=CommodityGroup.objects.filter(usages__in=application_usage),
        is_active=True,
    ).distinct()


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
