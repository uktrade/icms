from django.forms import CharField, ChoiceField
from django.forms.widgets import CheckboxInput, Textarea
from django_filters import BooleanFilter, CharFilter, ChoiceFilter, DateFilter, ModelChoiceFilter
from django_filters.fields import ModelChoiceField
from web.forms import ModelEditForm, ModelSearchFilter
from web.forms.widgets import DateInput

from .models import Commodity, CommodityGroup, CommodityType, Unit


class CommodityFilter(ModelSearchFilter):
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


class CommodityForm(ModelEditForm):
    commodity_code = CharField(label="Commodity Code")

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
            "validity_start_date": "First day of validity",
            "validity_end_date": "Last day of validity",
            "sigl_product_type": "SIGL Product Type",
        }
        help_texts = {
            "validity_start_date": "The commodity code will be available for applications to choose \
            on applications forms, starting on this date",
            "validity_end_date": "After this date, the commodity will no \
            longer be available for applications to choose on application \
            forms. Leave blank for indefinitely continuing validity",
            "quantity_threshold": "Quantity threshold is only necessary \
            for Iron, Steel and Aluminium commodities",
        }
        widgets = {"validity_start_date": DateInput, "validity_end_date": DateInput}


class CommodityEditForm(CommodityForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commodity_code"].disabled = True


class CommodityGroupFilter(ModelSearchFilter):
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


class CommodityGroupForm(ModelEditForm):
    group_type = ChoiceField(
        choices=CommodityGroup.TYPES,
        help_text="Auto groups will include all commodities beginning with the \
        Group Code. Category groups will allow you manually include \
        commodities",
    )
    commodity_type = ModelChoiceField(
        queryset=CommodityType.objects.all(),
        help_text="Please choose what type of commodities this group \
        should contain",
    )

    class Meta:
        model = CommodityGroup
        fields = ["group_type", "commodity_type", "group_code", "group_description"]
        labels = {
            "group_type": "Group Type",
            "commodity_type": "Commodity Types",
            "group_code": "Group Code",
            "group_description": "Group Description",
        }
        help_texts = {
            "group_code": "For Auto Groups: please enter the first four digits \
            of the commodity code you want to include in this group.\
            For Caegory Groups: enter the code that will identify this \
            category. This can be override by the Group Name below."
        }
        widgets = {"group_description": Textarea(attrs={"rows": 5, "cols": 20})}


class CommodityGroupEditForm(CommodityGroupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group_type"].disabled = True
        self.fields["commodity_type"].disabled = True
