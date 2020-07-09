from django.db.models import Count
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.forms.widgets import CheckboxInput, HiddenInput
from django_filters import BooleanFilter, CharFilter
from web.forms import ModelEditForm, ModelSearchFilter, ModelDisplayForm

from .models import ObsoleteCalibre, ObsoleteCalibreGroup


class ObsoleteCalibreGroupFilter(ModelSearchFilter):
    group_name = CharFilter(
        field_name="name", lookup_expr="icontains", label="Obsolete Calibre Group Name"
    )

    calibre_name = CharFilter(
        field_name="calibres__name", lookup_expr="icontains", label="Obsolete Calibre Name"
    )

    display_archived = BooleanFilter(
        label="Display Archived", widget=CheckboxInput, method="filter_display_archived"
    )

    def filter_display_archived(self, queryset, name, value):
        if value:
            return queryset

        # filter archived calibre groups
        return queryset.filter(is_active=True)

    @property
    def qs(self):
        self.queryset = ObsoleteCalibreGroup.objects.annotate(Count("calibres"))

        #  Filter archived querysets on first load as django_filters doesn't
        #  seem to apply filters on first load
        if not self.form.data:  # first page load
            self.queryset = self.queryset.filter(is_active=True)

        return super().qs

    class Meta:
        model = ObsoleteCalibreGroup
        fields = []


class ObsoleteCalibreGroupEditForm(ModelEditForm):
    class Meta:
        model = ObsoleteCalibreGroup
        fields = ["name"]
        labels = {"name": "Group Name"}


class ObsoleteCalibreGroupDisplayForm(ModelDisplayForm):
    class Meta(ObsoleteCalibreGroupEditForm.Meta):
        pass


class ObsoleteCalibreForm(ModelEditForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = ObsoleteCalibre
        fields = ["name", "order"]
        widgets = {"order": HiddenInput()}


class ObsoleteCalibreFormSet(BaseInlineFormSet):
    def sorted_forms(self):
        return sorted(self.forms, key=lambda form: form.instance.order)


def new_calibres_formset(instance, queryset=None, data=None, extra=0):
    initial = None
    if extra:
        initial = [{"order": 1}]
    return inlineformset_factory(
        ObsoleteCalibreGroup,
        ObsoleteCalibre,
        form=ObsoleteCalibreForm,
        formset=ObsoleteCalibreFormSet,
        extra=extra,
        can_delete=False,
    )(data, initial=initial, queryset=queryset, prefix="calibre", instance=instance)
