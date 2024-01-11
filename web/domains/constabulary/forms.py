from typing import Any

from django.forms import ModelChoiceField, ModelForm
from django.forms.widgets import CheckboxInput, Select
from django_filters import BooleanFilter, CharFilter, ChoiceFilter, FilterSet
from django_select2.forms import ModelSelect2Widget

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
        fields: list[Any] = []

    @property
    def form(self):
        form = super().form
        form.fields["name"] = ModelChoiceField(
            queryset=Constabulary.objects.all(),
            label="Constabulary Name",
            widget=ModelSelect2Widget(
                attrs={
                    "data-minimum-input-length": 0,
                    "data-placeholder": "-- Select Constabulary Name",
                },
                search_fields=("name__icontains",),
            ),
        )

        return form


class ConstabularyForm(ModelForm):
    class Meta:
        model = Constabulary
        fields = ["name", "region", "email"]
        widgets = {"region": Select(choices=Constabulary.REGIONS)}
