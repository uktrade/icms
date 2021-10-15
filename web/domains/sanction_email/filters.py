from typing import TYPE_CHECKING

import django_filters
from django.forms.widgets import CheckboxInput

from web.domains.mailshot.models import Mailshot

from . import models

if TYPE_CHECKING:
    from django.db.models import QuerySet


class SanctionEmailsFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains", label="Name")
    email = django_filters.CharFilter(
        field_name="email", lookup_expr="icontains", label="Email Address"
    )

    is_archived = django_filters.BooleanFilter(
        field_name="is_active",
        lookup_expr="exact",
        exclude=True,  # if checked get non active
        widget=CheckboxInput,
        label="Search Archived",
    )

    class Meta:
        model = models.SanctionEmail
        fields = ["name", "email", "is_archived"]

    @property
    def qs(self) -> "QuerySet[Mailshot]":
        qs = super().qs

        # initial state - filter form not submitted
        if not self.data:
            return qs.filter(is_active=True)

        # filter form submitted - fields will alter the query
        else:
            return qs
