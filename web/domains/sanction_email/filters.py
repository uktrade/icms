import django_filters

from . import models


class SanctionEmailsFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains", label="Name")
    email = django_filters.CharFilter(
        field_name="email", lookup_expr="icontains", label="Email Address"
    )

    class Meta:
        model = models.SanctionEmail
        fields = ["name", "email"]
