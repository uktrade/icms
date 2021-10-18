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
    )

    is_biocidal_claim = ChoiceFilter(
        field_name="is_biocidal_claim",
        choices=((True, "Yes"), (False, "No")),
        lookup_expr="exact",
        label="Is Biocidal Claim",
    )

    is_eu_cosmetics_regulation = ChoiceFilter(
        field_name="is_eu_cosmetics_regulation",
        choices=((True, "Yes"), (False, "No")),
        lookup_expr="exact",
        label="Is EU Cosmetics Regulation",
    )

    gb_legislation = ChoiceFilter(
        field_name="gb_legislation",
        choices=((True, "Yes"), (False, "No")),
        lookup_expr="exact",
        label="Great Britain Legislation",
    )

    ni_legislation = ChoiceFilter(
        field_name="ni_legislation",
        choices=((True, "Yes"), (False, "No")),
        lookup_expr="exact",
        label="Northern Ireland Legislation",
    )

    status = ChoiceFilter(
        field_name="is_active",
        choices=((True, "Current"), (False, "Archived")),
        lookup_expr="exact",
        label="Status",
    )

    class Meta:
        model = ProductLegislation
        fields = []


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
