from django.forms import (
    CharField,
    ChoiceField,
    DateField,
    Field,
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
from django_filters.fields import ModelChoiceField
from django.utils import timezone

from web.domains.commodity.widgets import CommodityWidget
from web.forms.widgets import DateInput

from .models import Commodity, CommodityGroup, CommodityType, Unit


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
        min_length=4,
        max_length=4,
        help_text="""
            For Auto Groups: please enter the first four digits
            of the commodity code you want to include in this group.
            For Category Groups: enter the code that will identify this
            category. This can be override by the Group Name below.
        """,
    )

    class Meta:
        model = CommodityGroup
        fields = ["group_type", "commodity_type", "group_code", "group_description", "commodities"]
        labels = {"group_description": "Group Description"}
        widgets = {"group_description": Textarea(attrs={"rows": 5, "cols": 20})}

    def clean(self):
        cleaned_data = super().clean()

        # Validate commodities in regard to commodity type and group type.
        # If group_type is:
        #  - CATEGORY user picks manually relevent commodities
        #  - AUTO the system sets the relevent commodities
        group_type = cleaned_data.get("group_type")
        commodity_type = cleaned_data.get("commodity_type")
        if group_type == CommodityGroup.CATEGORY:
            if not cleaned_data.get("commodities"):
                self.add_error("commodities", Field.default_error_messages["required"])
        elif group_type == CommodityGroup.AUTO and commodity_type:
            cleaned_data["commodities"] = Commodity.objects.filter(
                commodity_type__type=commodity_type.type
            )

        # Validate group code. Code shares 2 or 4 first characters from community type code.
        group_code = cleaned_data.get("group_code", "")
        if commodity_type and len(group_code) == 4:
            types = CommodityType.objects.filter(type=commodity_type.type)
            exists = types.filter(type_code__in=[group_code[:2], group_code[:4]]).exists()
            if not exists:
                self.add_error(
                    "group_code",
                    "This code is not of the selected type. Allowed code prefixes: {}".format(
                        ", ".join(types.values_list("type_code", flat=True))
                    ),
                )

        return cleaned_data


class CommodityGroupEditForm(CommodityGroupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group_type"].disabled = True
        self.fields["commodity_type"].disabled = True
