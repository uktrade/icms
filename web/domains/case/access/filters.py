from django.db.models import Q
from django_filters import CharFilter, ChoiceFilter, FilterSet

from web.models import ExporterAccessRequest, ImporterAccessRequest


class ImporterAccessRequestFilter(FilterSet):
    q = CharFilter(
        method="filter_access_request",
        label="Search",
        help_text="""
            Search Importer Access Requests. Results returned are matched against organisation name,
            organisation registered number, agent name, linked importer name and submitted by.
        """,
    )
    request_type = ChoiceFilter(
        choices=ImporterAccessRequest.REQUEST_TYPES,
        lookup_expr="exact",
        label="Request Type",
        empty_label="Any",
    )

    class Meta:
        model = ImporterAccessRequest
        fields = ("q", "request_type")

    def filter_access_request(self, queryset, name, value):
        return self.queryset.filter(
            Q(organisation_name__icontains=value)
            | Q(agent_name__icontains=value)
            | Q(organisation_registered_number__icontains=value)
            | Q(link__name__icontains=value)
            | Q(link__user__first_name__icontains=value)
            | Q(link__user__last_name__icontains=value)
            | Q(submitted_by__first_name__icontains=value)
            | Q(submitted_by__last_name__icontains=value)
        )


class ExporterAccessRequestFilter(FilterSet):
    q = CharFilter(
        method="filter_access_request",
        label="Search",
        help_text="""
            Search Exporter Access Requests. Results returned are matched against organisation name,
            organisation registered number, agent name, linked exporter name and submitted by.
        """,
    )
    request_type = ChoiceFilter(
        choices=ExporterAccessRequest.REQUEST_TYPES, lookup_expr="exact", label="Request Type"
    )

    class Meta:
        model = ExporterAccessRequest
        fields = ("q", "request_type")

    def filter_access_request(self, queryset, name, value):
        return self.queryset.filter(
            Q(organisation_name__icontains=value)
            | Q(agent_name__icontains=value)
            | Q(organisation_registered_number__icontains=value)
            | Q(link__name__icontains=value)
            | Q(submitted_by__first_name__icontains=value)
            | Q(submitted_by__last_name__icontains=value)
        )
