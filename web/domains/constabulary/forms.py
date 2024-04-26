from typing import Any

from django.forms import ModelChoiceField, ModelForm, ValidationError
from django.forms.widgets import CheckboxInput, Select
from django_filters import BooleanFilter, CharFilter, ChoiceFilter, FilterSet

from web.forms.widgets import ICMSModelSelect2Widget

from .models import Constabulary


class ConstabulariesFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains", label="Constabulary Name")

    region = ChoiceFilter(
        field_name="region",
        choices=Constabulary.REGIONS,
        lookup_expr="icontains",
        label="Constabulary Region",
        empty_label="Any",
    )

    email = CharFilter(field_name="email", lookup_expr="icontains", label="Email Address")

    telephone_number = CharFilter(
        field_name="telephone_number", lookup_expr="icontains", label="Telephone Number"
    )

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
            widget=ICMSModelSelect2Widget(
                attrs={
                    "data-minimum-input-length": 0,
                    "data-placeholder": "-- Select Constabulary Name",
                },
                search_fields=("name__icontains",),
            ),
            required=False,
        )

        return form


class ConstabularyForm(ModelForm):
    class Meta:
        model = Constabulary
        fields = ["name", "region", "email", "telephone_number"]
        widgets = {"region": Select(choices=Constabulary.REGIONS)}

    def clean_telephone_number(self):
        telephone_number = self.cleaned_data["telephone_number"]
        telephone_number = telephone_number.replace(" ", "")
        if not telephone_number.isdigit():
            raise ValidationError("Telephone number must contain only digits.")
        if not telephone_number.startswith("0"):
            raise ValidationError("Telephone number must start with 0.")
        if len(telephone_number) < 10:
            raise ValidationError("Telephone number must contain at least 10 digits.")
        return telephone_number
