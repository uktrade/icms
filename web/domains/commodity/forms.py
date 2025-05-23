from typing import Any

from django.forms import (
    CharField,
    ChoiceField,
    Field,
    ModelChoiceField,
    ModelForm,
    ModelMultipleChoiceField,
)
from django.forms.widgets import CheckboxInput, Textarea
from django.template.loader import render_to_string
from django.utils import timezone
from django_filters import (
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    Filter,
    FilterSet,
    ModelChoiceFilter,
)

from web.domains.commodity.widgets import CommodityGroupCommodityWidget
from web.forms.fields import JqueryDateField
from web.models import ImportApplicationType

from .models import Commodity, CommodityGroup, CommodityType, Unit, Usage
from .widgets import UsageCountryWidget


class JqueryDateFilter(Filter):
    field_class = JqueryDateField


# Used in application forms.
COMMODITY_HELP_TEXT = render_to_string("partial/commodity/commodity_help_text.html")


class CommodityFilter(FilterSet):
    commodity_code = CharFilter(
        field_name="commodity_code", lookup_expr="icontains", label="Commodity Code"
    )

    commodity_type = ModelChoiceFilter(
        queryset=CommodityType.objects.all(), label="Commodity Type", empty_label="Any"
    )

    valid_start = JqueryDateFilter(
        field_name="validity_start_date", lookup_expr="gte", label="Valid between"
    )

    valid_end = JqueryDateFilter(field_name="validity_end_date", lookup_expr="lte", label="and")

    is_archived = BooleanFilter(
        field_name="is_active",
        lookup_expr="exact",
        exclude=True,
        widget=CheckboxInput,
        label="Search Archived",
    )

    class Meta:
        model = Commodity
        fields: list[Any] = []


class CommodityForm(ModelForm):
    validity_start_date = JqueryDateField(
        required=True,
        label="First day of validity",
        help_text=(
            "The commodity code will be available for applications to"
            " choose on applications forms, starting on this date."
        ),
    )

    validity_end_date = JqueryDateField(
        required=False,
        label="Last day of validity",
        help_text=(
            "After this date, the commodity will no longer be available for"
            " applications to choose on application forms. Leave blank for"
            " indefinitely continuing validity."
        ),
    )

    class Meta:
        model = Commodity
        fields = [
            "commodity_code",
            "commodity_type",
            "validity_start_date",
            "validity_end_date",
            "quantity_threshold",
            "sigl_product_type",
        ]
        labels = {
            "commodity_code": "Commodity Code",
            "sigl_product_type": "SIGL Product Type",
        }
        help_texts = {
            "quantity_threshold": "Quantity threshold is only necessary for Iron, Steel and Aluminium commodities.",
            "sigl_product_type": "Mandatory for Iron, Steel, Aluminium and Textile commodities.",
        }


class CommodityEditForm(CommodityForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commodity_code"].disabled = True


class CommodityGroupFilter(FilterSet):
    group_type = ChoiceFilter(
        field_name="group_type",
        choices=CommodityGroup.TYPES,
        label="Group Type",
        empty_label="Any",
    )
    commodity_type = ModelChoiceFilter(
        queryset=CommodityType.objects.all(),
        label="Commodity Type",
        empty_label="Any",
    )
    group_code = CharFilter(field_name="group_code", lookup_expr="icontains", label="Group Code")
    group_name = CharFilter(field_name="group_name", lookup_expr="icontains", label="Group Name")
    group_description = CharFilter(
        field_name="group_description", lookup_expr="icontains", label="Group Description"
    )
    commodity_code = CharFilter(
        field_name="commodities__commodity_code", lookup_expr="icontains", label="Commodity Code"
    )
    unit = ModelChoiceFilter(
        queryset=Unit.objects.exclude(
            # Exclude a few of the new types that we will probably never need
            unit_type__in=["Length", "Various"]
        ).order_by("hmrc_code"),
        empty_label="Any",
    )
    application_type = ModelChoiceFilter(
        queryset=ImportApplicationType.objects.filter(is_active=True),
        field_name="usages__application_type",
        label="Application Type",
        help_text=(
            "Shows all commodity group usages relating to the chosen application type."
            " Mainly useful for Sanctions and Adhoc Licence Application"
        ),
    )
    is_archived = BooleanFilter(
        field_name="is_active",
        widget=CheckboxInput,
        lookup_expr="exact",
        exclude=True,
        label="Search Archived",
    )

    class Meta:
        model = CommodityGroup
        fields: list[Any] = []


class CommodityGroupForm(ModelForm):
    GROUP_TYPE_CHOICES = [("", "---------")] + CommodityGroup.TYPES

    group_type = ChoiceField(
        label="Group Type",
        choices=GROUP_TYPE_CHOICES,
        help_text="""
            Auto groups will include all commodities beginning with the
            Group Code. Category groups will allow you manually include
            commodities.
        """,
    )
    commodity_type = ModelChoiceField(
        label="Commodity Types",
        queryset=CommodityType.objects.all(),
        help_text="Please choose what type of commodities this group should contain.",
    )
    commodities = ModelMultipleChoiceField(
        label="Commodity Code",
        queryset=Commodity.objects.all().select_related("commodity_type"),
        widget=CommodityGroupCommodityWidget,
        required=False,
    )
    group_code = CharField(
        label="Group Code",
        help_text="""
            For Auto Groups: please enter the first four digits
            of the commodity code you want to include in this group.
            For Category Groups: enter the code that will identify this
            category. This can be override by the Group Name below.
        """,
    )

    class Meta:
        model = CommodityGroup
        fields = [
            "group_type",
            "commodity_type",
            "group_code",
            "group_name",
            "group_description",
            "commodities",
            "unit",
        ]
        labels = {"group_description": "Group Description", "group_name": "Display Name"}
        widgets = {"group_description": Textarea(attrs={"rows": 5, "cols": 20})}

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        group_type = cleaned_data.get("group_type")

        # Ensure unit is filled when CommodityGroup.group_type is CATEGORY
        if group_type == CommodityGroup.CATEGORY:
            if not cleaned_data.get("unit"):
                self.add_error("unit", Field.default_error_messages["required"])
        elif group_type == CommodityGroup.AUTO:
            cleaned_data.pop("unit", None)

            #  - CommodityGroup.group_code should be 4 characters long
            group_code = cleaned_data.get("group_code", "")
            if group_type == CommodityGroup.AUTO and len(group_code) != 4:
                self.add_error("group_code", "Group Code should be four characters long")
        return cleaned_data


class CommodityGroupEditForm(CommodityGroupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group_type"].disabled = True
        self.fields["commodity_type"].disabled = True


class UsageForm(ModelForm):
    commodity_group = ModelChoiceField(disabled=True, queryset=CommodityGroup.objects.none())
    start_date = JqueryDateField(required=True)
    end_date = JqueryDateField(required=False)

    class Meta:
        model = Usage
        fields = [
            "commodity_group",
            "application_type",
            "country",
            "start_date",
            "end_date",
            "maximum_allocation",
        ]
        help_texts = {
            "maximum_allocation": """
                Optionally enter the maximum allocation of commodities in this group an applicant
                may request (textile and outward processing trade applications only). The applicant
                will be asked to provide evidence of past trade if they exceed this limit. Leave
                blank to apply no maximum.
            """,
        }
        widgets = {
            "country": UsageCountryWidget(
                attrs={
                    "data-minimum-input-length": 0,
                    "data-placeholder": "Pick an Application Type to see available countries",
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial.get("commodity_group"):
            self.fields["commodity_group"].queryset = CommodityGroup.objects.filter(
                pk=self.initial["commodity_group"]
            )

        # Include inactive for historical usage records
        self.fields["application_type"].queryset = ImportApplicationType.objects.all()

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        if self.errors:
            return cleaned_data

        application_type = cleaned_data["application_type"]
        country = cleaned_data["country"]
        commodity_group = cleaned_data["commodity_group"]
        start_date = cleaned_data["start_date"]
        end_date = cleaned_data["end_date"]

        today = timezone.now().date()
        if end_date:
            if end_date <= start_date:
                self.add_error("end_date", "End date must be after the start date")

            if end_date < today:
                self.add_error("end_date", "End date must be today or in the future")

        related_usage = Usage.objects.filter(
            country=country, application_type=application_type, commodity_group=commodity_group
        ).order_by("-start_date")

        if self.instance.pk is not None:
            related_usage = related_usage.exclude(pk=self.instance.pk)

        latest = related_usage.first()

        if latest:
            if start_date < latest.start_date:
                self.add_error("start_date", "Start date is before previous start date")

            if latest.end_date and start_date < latest.end_date:
                self.add_error("start_date", "Start date is before previous end date")

            if not latest.end_date:
                self.add_error("end_date", "Previous end date has not been set.")

            if end_date and latest.end_date and end_date < latest.end_date:
                self.add_error("end_date", "End date is before previous end date.")

        return cleaned_data
