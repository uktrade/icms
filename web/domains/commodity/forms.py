from django.forms import (
    CharField,
    ChoiceField,
    Field,
    ModelChoiceField,
    ModelForm,
    ModelMultipleChoiceField,
)
from django.forms.widgets import CheckboxInput, Textarea
from django_filters import (
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    DateFilter,
    FilterSet,
    ModelChoiceFilter,
)

from web.domains.case._import.models import ImportApplicationType
from web.domains.commodity.widgets import CommodityGroupCommodityWidget
from web.forms.widgets import DateInput

from .models import Commodity, CommodityGroup, CommodityType, Unit, Usage


class CommodityFilter(FilterSet):
    commodity_code = CharFilter(
        field_name="commodity_code", lookup_expr="icontains", label="Commodity Code"
    )

    valid_start = DateFilter(
        field_name="validity_start_date", lookup_expr="gte", widget=DateInput, label="Valid between"
    )

    valid_end = DateFilter(
        field_name="validity_end_date", lookup_expr="lte", widget=DateInput, label="and"
    )

    is_archived = BooleanFilter(
        field_name="is_active",
        lookup_expr="exact",
        exclude=True,
        widget=CheckboxInput,
        label="Search Archived",
    )

    class Meta:
        model = Commodity
        fields = []


class CommodityForm(ModelForm):
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
            "validity_start_date": "First day of validity",
            "validity_end_date": "Last day of validity",
            "sigl_product_type": "SIGL Product Type",
        }
        help_texts = {
            "validity_start_date": (
                "The commodity code will be available for applications to"
                " choose on applications forms, starting on this date."
            ),
            "validity_end_date": (
                "After this date, the commodity will no longer be available for"
                " applications to choose on application forms. Leave blank for"
                " indefinitely continuing validity."
            ),
            "quantity_threshold": "Quantity threshold is only necessary for Iron, Steel and Aluminium commodities.",
            "sigl_product_type": "Mandatory for Iron, Steel, Aluminium and Textile commodities.",
        }
        widgets = {"validity_start_date": DateInput, "validity_end_date": DateInput}


class CommodityEditForm(CommodityForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commodity_code"].disabled = True


class CommodityGroupFilter(FilterSet):
    group_type = ChoiceFilter(
        field_name="group_type", choices=CommodityGroup.TYPES, label="Group Type"
    )
    commodity_type = ModelChoiceFilter(
        queryset=CommodityType.objects.all(), label="Commodity Types"
    )

    application_type = ModelChoiceFilter(
        queryset=ImportApplicationType.objects.filter(is_active=True),
        field_name="usages__application_type",
        label="Application Type",
    )

    group_code = CharFilter(field_name="group_code", lookup_expr="icontains", label="Group Code")
    group_name = CharFilter(field_name="group_name", lookup_expr="icontains", label="Group Name")
    group_description = CharFilter(
        field_name="group_description", lookup_expr="icontains", label="Group Description"
    )
    commodity_code = CharFilter(
        field_name="commodities__commodity_code", lookup_expr="icontains", label="Commodity Code"
    )
    unit = ModelChoiceFilter(queryset=Unit.objects.all())

    is_archived = BooleanFilter(
        field_name="is_active",
        widget=CheckboxInput,
        lookup_expr="exact",
        exclude=True,
        label="Search Archived",
    )

    class Meta:
        model = CommodityGroup
        fields = []


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
        queryset=Commodity.objects.all(),
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

    def clean(self):
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


class CommodityGroupEditForm(CommodityGroupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group_type"].disabled = True
        self.fields["commodity_type"].disabled = True


class UsageForm(ModelForm):
    commodity_group = ModelChoiceField(disabled=True, queryset=CommodityGroup.objects.none())

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
        widgets = {"start_date": DateInput, "end_date": DateInput}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial.get("commodity_group"):
            self.fields["commodity_group"].queryset = CommodityGroup.objects.filter(
                pk=self.initial["commodity_group"]
            )

        self.fields["application_type"].queryset = ImportApplicationType.objects.filter(
            is_active=True
        )
