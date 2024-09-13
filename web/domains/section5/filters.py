from django.forms.widgets import CheckboxInput
from django_filters import BooleanFilter, CharFilter, FilterSet


class Section5Filter(FilterSet):
    clause = CharFilter(lookup_expr="icontains", label="Clause")
    description = CharFilter(lookup_expr="icontains", label="Description")
    is_archived = BooleanFilter(
        field_name="is_active",
        lookup_expr="exact",
        exclude=True,
        widget=CheckboxInput,
        label="Search Archived",
    )
