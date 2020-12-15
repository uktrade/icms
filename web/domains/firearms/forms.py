from django.forms import ModelForm
from django.forms.widgets import CheckboxInput
from django_filters import BooleanFilter, CharFilter, ChoiceFilter, FilterSet

from .models import ObsoleteCalibre, ObsoleteCalibreGroup


class ObsoleteCalibreGroupFilter(FilterSet):
    group_name = ChoiceFilter(
        field_name="name",
        label="Obsolete Calibre Group Name",
        lookup_expr="exact",
        empty_label="Any",
    )

    calibre_name = CharFilter(
        field_name="calibres__name", lookup_expr="icontains", label="Obsolete Calibre Name"
    )

    display_archived = BooleanFilter(
        label="Display Archived", widget=CheckboxInput, method="filter_display_archived"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ModelChoiceFilter only works for FKs
        self.filters["group_name"].extra["choices"] = (
            (row.name, row.name) for row in ObsoleteCalibreGroup.objects.filter(is_active=True)
        )

    def filter_display_archived(self, queryset, name, value):
        return queryset

    class Meta:
        model = ObsoleteCalibreGroup
        fields = ["group_name", "calibre_name"]


class ObsoleteCalibreGroupForm(ModelForm):
    class Meta:
        model = ObsoleteCalibreGroup
        fields = ["name"]
        labels = {"name": "Group Name"}


class ObsoleteCalibreForm(ModelForm):
    class Meta:
        model = ObsoleteCalibre
        fields = ["name"]
        labels = {"name": "Calibre Name"}
