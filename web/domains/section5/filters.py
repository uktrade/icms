from django_filters import CharFilter, FilterSet

from web.domains.section5.models import Section5Clause


class Section5Filter(FilterSet):
    clause = CharFilter(lookup_expr="icontains", label="Clause")
    description = CharFilter(lookup_expr="icontains", label="Description")

    class Meta:
        model = Section5Clause
        fields = ("clause", "description")
