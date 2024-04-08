from typing import Any

from django.forms import ModelForm
from django_filters import CharFilter, ChoiceFilter, FilterSet

from .models import ProductLegislation


class ProductLegislationFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains", label="Legislation Name")

    is_biocidal = ChoiceFilter(
        field_name="is_biocidal",
        choices=((True, "Yes"), (False, "No")),
        lookup_expr="exact",
        label="Is Biocidal",
        empty_label="Any",
    )

    is_biocidal_claim = ChoiceFilter(
        field_name="is_biocidal_claim",
        choices=((True, "Yes"), (False, "No")),
        lookup_expr="exact",
        label="Is Biocidal Claim",
        empty_label="Any",
    )

    is_eu_cosmetics_regulation = ChoiceFilter(
        field_name="is_eu_cosmetics_regulation",
        choices=((True, "Yes"), (False, "No")),
        lookup_expr="exact",
        label="Is EU Cosmetics Regulation",
        empty_label="Any",
    )

    gb_legislation = ChoiceFilter(
        field_name="gb_legislation",
        choices=((True, "Yes"), (False, "No")),
        lookup_expr="exact",
        label="Great Britain Legislation",
        empty_label="Any",
    )

    ni_legislation = ChoiceFilter(
        field_name="ni_legislation",
        choices=((True, "Yes"), (False, "No")),
        lookup_expr="exact",
        label="Northern Ireland Legislation",
        empty_label="Any",
    )

    status = ChoiceFilter(
        field_name="is_active",
        choices=((True, "Current"), (False, "Archived")),
        lookup_expr="exact",
        label="Status",
        empty_label="Any",
    )

    class Meta:
        model = ProductLegislation
        fields: list[Any] = []

    @property
    def form(self):
        form = super().form
        form.fields["status"].initial = True
        return form


class ProductLegislationForm(ModelForm):
    class Meta:
        model = ProductLegislation
        fields = [
            "name",
            "is_biocidal",
            "is_biocidal_claim",
            "is_eu_cosmetics_regulation",
            "gb_legislation",
            "ni_legislation",
        ]
