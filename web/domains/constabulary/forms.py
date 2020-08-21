from django.forms import ModelForm
from django.forms.widgets import Select, CheckboxInput
from django_filters import CharFilter, ChoiceFilter, BooleanFilter, FilterSet

from .models import Constabulary


class ConstabulariesFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains", label="Constabulary Name")

    region = ChoiceFilter(
        field_name="region",
        choices=Constabulary.REGIONS,
        lookup_expr="icontains",
        label="Constabulary Region",
    )

    email = CharFilter(field_name="email", lookup_expr="icontains", label="Email Address")

    archived = BooleanFilter(
        field_name="is_active",
        lookup_expr="exact",
        widget=CheckboxInput,
        label="Search Archived",
        exclude=True,
    )

    class Meta:
        model = Constabulary
        fields = []


class ConstabularyForm(ModelForm):
    class Meta:
        model = Constabulary
        fields = ["name", "region", "email"]
        widgets = {"region": Select(choices=Constabulary.REGIONS)}
