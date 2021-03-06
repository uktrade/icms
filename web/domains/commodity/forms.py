from django.db.models import Q
from django.forms import (
    CharField,
    ChoiceField,
    DateField,
    Field,
    ModelChoiceField,
    ModelForm,
    ModelMultipleChoiceField,
)
from django.forms.widgets import CheckboxInput, Textarea
from django.utils import timezone
from django_filters import (
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    DateFilter,
    FilterSet,
    ModelChoiceFilter,
)

from web.domains.commodity.widgets import CommodityWidget
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
    commodity_code = CharField(label="Commodity Code", min_length=10)
    validity_start_date = DateField(
        label="First day of validity",
        initial=timezone.now(),
        help_text="""
            The commodity code will be available for applications to choose
            on applications forms, starting on this date.
        """,
    )

    class Meta:
        model = Commodity
        fields = [
            "commodity_code",
            "validity_start_date",
            "validity_end_date",
            "quantity_threshold",
            "sigl_product_type",
        ]
        labels = {
            "validity_end_date": "Last day of validity",
            "sigl_product_type": "SIGL Product Type",
        }
        help_texts = {
            "validity_end_date": """
                After this date, the commodity will no
                longer be available for applications to choose on application
                forms. Leave blank for indefinitely continuing validity.
            """,
            "quantity_threshold": "Quantity threshold is only necessary for Iron, Steel and Aluminium commodities.",
            "sigl_product_type": "Mandatory for Iron, Steel, Aluminium and Textile commodities.",
        }
        widgets = {"validity_start_date": DateInput, "validity_end_date": DateInput}

    def clean(self):
        data = super().clean()
        self.commodity_types = CommodityType.objects.filter(
            Q(allowed_codes__contains=[data["commodity_code"][:2]])
            | Q(allowed_codes__contains=[data["commodity_code"][:4]])
        )
        if not self.commodity_types.exists():
            self.add_error("commodity_code", "Commodity Type for code doesn't exist")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.commodity_type = self.commodity_types.first()
        if commit:
            instance.save()
        return instance


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
        queryset=CommodityType.objects.distinct("type").all(),
        help_text="Please choose what type of commodities this group should contain.",
    )
    commodities = ModelMultipleChoiceField(
        label="Commodity Code",
        queryset=Commodity.objects.all(),
        widget=CommodityWidget,
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

            #  - CommodityGroup.group_code should match or start with CommodityType.allowed_codes
            commodity_type = cleaned_data.get("commodity_type")
            if len(group_code) == 4:
                if (
                    group_code[:2] not in commodity_type.allowed_codes
                    and group_code not in commodity_type.allowed_codes
                ):
                    self.add_error(
                        "group_code",
                        "This code is not of the selected type. Allowed code prefixes: {}".format(
                            ", ".join(commodity_type.allowed_codes)
                        ),
                    )


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
            "start_datetime",
            "end_datetime",
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
            "start_datetime": DateInput(),
            "end_datetime": DateInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial.get("commodity_group"):
            self.fields["commodity_group"].queryset = CommodityGroup.objects.filter(
                pk=self.initial["commodity_group"]
            )
