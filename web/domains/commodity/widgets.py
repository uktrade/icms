from typing import Any

from django.db.models.query import QuerySet

from web.domains.country.types import CountryGroupName
from web.forms.widgets import ICMSModelSelect2MultipleWidget, ICMSModelSelect2Widget
from web.models import Country, ImportApplicationType
from web.types import AuthenticatedHttpRequest


class CommodityWidget(ICMSModelSelect2MultipleWidget):
    # The value entered by the user is used to search the commodity code
    search_fields = ["commodity_code__contains"]

    def label_from_instance(self, commodity):
        return "{code} {code_type} {start_date} {end_date}".format(
            code=commodity.commodity_code,
            code_type=commodity.commodity_type,
            start_date=commodity.validity_start_date or "",
            end_date=commodity.validity_end_date or "",
        )


class CommodityGroupCommodityWidget(CommodityWidget):
    """Used when creating / editing commodity groups"""

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {"commodity_type": "commodity_type"}


class UsageCountryWidget(ICMSModelSelect2Widget):
    """Used when creating usage records"""

    queryset = Country.objects.all().filter(is_active=True)

    # The value entered by the user is used to search the commodity code
    search_fields = ["name__contains"]

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {"application_type": "application_type"}

    def filter_queryset(
        self,
        request: AuthenticatedHttpRequest,
        term: str,
        queryset: QuerySet | None = None,
        **dependent_fields: Any,
    ) -> QuerySet[Country]:
        """Filter the available countries depending on the application type selected by the user."""

        if queryset is None:
            queryset = self.get_queryset()

        application_type_pk: str | None = dependent_fields.get("application_type")

        if not application_type_pk:
            return queryset.none()

        group_name = self._get_country_of_origin_group_name(application_type_pk)

        return queryset.filter(country_groups__name=group_name)

    def _get_country_of_origin_group_name(self, app_type_pk: str) -> str:
        application_type = ImportApplicationType.objects.get(pk=int(app_type_pk))

        types = ImportApplicationType.Types
        subtypes = ImportApplicationType.SubTypes

        match (application_type.type, application_type.sub_type):
            #
            # Active Application types
            #
            case (types.FIREARMS, subtypes.OIL):
                group_name = CountryGroupName.FA_OIL_COO
            case (types.FIREARMS, subtypes.DFL):
                group_name = CountryGroupName.FA_DFL_IC
            case (types.FIREARMS, subtypes.SIL):
                group_name = CountryGroupName.FA_SIL_COO
            case (types.SANCTION_ADHOC, _):
                group_name = CountryGroupName.SANCTIONS_COC_COO
            case (types.WOOD_QUOTA, _):
                group_name = CountryGroupName.WOOD_COO
            #
            # Inactive Application types
            #
            case (types.DEROGATION, _):
                group_name = CountryGroupName.DEROGATION_FROM_SANCTION_COO
            case (types.IRON_STEEL, _):
                group_name = CountryGroupName.IRON
            case (types.OPT, _):
                group_name = CountryGroupName.OPT_COO
            case (types.SPS, _):
                group_name = CountryGroupName.NON_EU
            case (types.TEXTILES, _):
                group_name = CountryGroupName.TEXTILES_COO
            case _:
                raise ValueError(
                    f"Can't get group name for {application_type.type}, {application_type.sub_type}"
                )

        return group_name
