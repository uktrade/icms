from typing import TYPE_CHECKING, Iterable

from django.db.models import F
from django.db.models.functions import Coalesce
from django.utils import timezone

from web.domains.case._import.models import ImportApplicationType
from web.domains.commodity.models import Usage

if TYPE_CHECKING:
    from django.db.models import QuerySet


def get_usage_records(app_type: str, app_sub_type: str = None):
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


def get_country_of_origin_choices(
    application_usage: "QuerySet[Usage]",
) -> Iterable[tuple[int, str]]:
    """Get country of origin choices for forms."""

    application_usage = (
        application_usage.select_related("country")
        .values_list("country__pk", "country__name")
        .order_by("country__name")
    )

    return (r for r in application_usage)
