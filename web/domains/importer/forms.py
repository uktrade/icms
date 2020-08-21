from django.forms import ChoiceField, CharField, ModelForm
from django_filters import CharFilter, ChoiceFilter, FilterSet
from web.forms.mixins import ReadonlyFormMixin
from django.db.models import Q

from .models import Importer


class ImporterFilter(FilterSet):
    importer_entity_type = ChoiceFilter(
        field_name="type", choices=Importer.TYPES, label="Importer Entity Type"
    )

    status = ChoiceFilter(
        field_name="is_active",
        choices=((True, "Current"), (False, "Archived")),
        lookup_expr="exact",
        label="Status",
    )

    name = CharFilter(lookup_expr="icontains", label="Importer Name", method="filter_importer_name")

    agent_name = CharFilter(lookup_expr="icontains", label="Agent Name", method="filter_agent_name")

    # Filter base queryset to only get importers that are not agents.
    @property
    def qs(self):
        return super().qs.filter(main_importer__isnull=True)

    def filter_importer_name(self, queryset, name, value):
        if not value:
            return queryset

        #  Filter organisation name for organisations and title, first_name, last_name
        #  for individual importers
        return queryset.filter(
            Q(name__icontains=value)
            | Q(user__title__icontains=value)
            | Q(user__first_name__icontains=value)
            | Q(user__last_name__icontains=value)
        )

    def filter_agent_name(self, queryset, name, value):
        if not value:
            return queryset

        #  Filter agent name for organisations and title, first_name, last_name
        #  for individual importer agents
        return queryset.filter(
            Q(agents__name__icontains=value)
            | Q(agents__user__title__icontains=value)
            | Q(agents__user__first_name__icontains=value)
            | Q(agents__user__last_name__icontains=value)
        )

    class Meta:
        model = Importer
        fields = []


class ImporterOrganisationEditForm(ModelForm):
    type = ChoiceField(choices=Importer.TYPES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True

    class Meta:
        model = Importer
        fields = ["type", "name", "region_origin", "comments"]
        labels = {"type": "Entity Type"}


class ImporterOrganisationDisplayForm(ReadonlyFormMixin, ImporterOrganisationEditForm):
    pass


class ImporterIndividualEditForm(ModelForm):
    type = ChoiceField(choices=Importer.TYPES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].required = True

    class Meta:
        model = Importer
        fields = ["type", "user", "comments"]


class ImporterIndividualDisplayForm(ReadonlyFormMixin, ModelForm):
    type = ChoiceField(choices=Importer.TYPES)

    # ImporterIndividualDetailView fills these out
    user_title = CharField(label="Title")
    user_first_name = CharField(label="Forename")
    user_last_name = CharField(label="Surname")
    user_email = CharField(label="Email")
    user_tel_no = CharField(label="Telephone No")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].required = True

    class Meta:
        model = Importer
        fields = ["type", "user", "comments"]
