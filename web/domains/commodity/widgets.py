from django.db.models.query import QuerySet
from django.http import HttpRequest
from django_select2 import forms as s2forms

from web.domains.case._import.models import ImportApplicationType
from web.domains.commodity.models import Country


class CommodityWidget(s2forms.ModelSelect2MultipleWidget):
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


class UsageCountryWidget(s2forms.ModelSelect2Widget):
    """Used when creating usage records"""

    queryset = Country.objects.all().filter(is_active=True)

    # The value entered by the user is used to search the commodity code
    search_fields = ["name__contains"]

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {"application_type": "application_type"}

    def filter_queryset(
        self,
        request: HttpRequest,
        term: str,
        queryset: QuerySet | None = None,
        **dependent_fields,
    ) -> QuerySet:
        """Filter the available countries depending on the application type selected by the user."""

        if queryset is None:
            queryset = self.get_queryset()

        application_type: str | None = dependent_fields.get("application_type")

        if not application_type:
            return queryset.none()

        group_name = self._get_country_of_origin_group_name(application_type)

        return queryset.filter(country_groups__name=group_name)

    def _get_country_of_origin_group_name(self, app_type):
        application_type = ImportApplicationType.objects.get(pk=app_type)

        types = ImportApplicationType.Types
        subtypes = ImportApplicationType.SubTypes

        mapped_types = {
            types.DEROGATION: "Derogation from Sanctions COOs",
            types.IRON_STEEL: "Iron and Steel (Quota) COOs",
            types.OPT: "OPT COOs",
            types.SANCTION_ADHOC: "Sanctions and Adhoc License",
            types.SPS: "Non EU Single Countries",
            types.TEXTILES: "Textile COOs",
            types.WOOD_QUOTA: "Wood (Quota) COOs",
        }

        mapped_types_with_subtypes = {
            types.FIREARMS: {
                subtypes.OIL: "Firearms and Ammunition (OIL) COOs",
                subtypes.DFL: "Firearms and Ammunition (Deactivated) Issuing Countries",
                subtypes.SIL: "Firearms and Ammunition (SIL) COOs",
            }
        }

        if application_type.type in mapped_types.keys():
            group_name = mapped_types[application_type.type]
        elif application_type.type in mapped_types_with_subtypes.keys():
            group_name = mapped_types_with_subtypes[application_type.type][
                application_type.sub_type
            ]
        else:
            raise NotImplementedError(
                f"Can't get group name for {application_type.type}, {application_type.sub_type}"
            )

        return group_name
