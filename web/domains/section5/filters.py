from django_filters import BooleanFilter, CharFilter, FilterSet

from web.domains.section5.models import Section5Clause


class Section5Filter(FilterSet):
    clause = CharFilter(lookup_expr="icontains", label="Clause")
    description = CharFilter(lookup_expr="icontains", label="Description")

    is_active = BooleanFilter(
        field_name="is_active",
        lookup_expr="exact",
        label="Search Archived",
        exclude=True,
    )

    class Meta:
        model = Section5Clause
        fields = ("clause", "description", "is_active")
