from django.core.exceptions import ValidationError
from django.forms import ChoiceField, CharField, ModelChoiceField, ModelForm
from django_filters import CharFilter, ChoiceFilter, FilterSet
from django.db.models import Q

from web.domains.importer.fields import PersonWidget
from web.domains.importer.models import Importer
from web.domains.user.models import User
from web.forms.mixins import ReadonlyFormMixin


class ImporterIndividualForm(ModelForm):
    user = ModelChoiceField(
        queryset=User.objects.importer_access(),
        widget=PersonWidget,
        help_text="""
            Search a user to link. Users returned are matched against first/last name,
            email and title.
        """,
    )

    class Meta:
        model = Importer
        fields = ["user", "eori_number", "eori_number_ni", "region_origin", "comments"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["eori_number"].required = True

    def clean(self):
        """Set type as individual as Importer can be an organisation too."""
        self.instance.type = Importer.INDIVIDUAL
        return super().clean()

    def clean_eori_number(self):
        """Make sure eori number starts with GBPR."""
        eori_number = self.cleaned_data["eori_number"]
        prefix = "GBPR"
        if eori_number.startswith(prefix):
            return eori_number
        raise ValidationError(f"'{eori_number}' doesn't start with {prefix}")


class ImporterOrganisationForm(ModelForm):
    class Meta:
        model = Importer
        fields = [
            "name",
            "registered_number",
            "eori_number",
            "eori_number_ni",
            "region_origin",
            "comments",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["eori_number"].required = True

    def clean(self):
        """Set type as organisation as Importer can be an individual too."""
        self.instance.type = Importer.ORGANISATION
        return super().clean()

    def clean_eori_number(self):
        """Make sure eori number starts with GB."""
        eori_number = self.cleaned_data["eori_number"]
        prefix = "GB"
        if eori_number.startswith(prefix):
            return eori_number
        raise ValidationError(f"'{eori_number}' doesn't start with {prefix}")


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


class ImporterOrganisationDisplayForm(ReadonlyFormMixin, ModelForm):
    type = ChoiceField(choices=Importer.TYPES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True

    class Meta:
        model = Importer
        fields = ["type", "name", "region_origin", "comments"]
        labels = {"type": "Entity Type"}


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


class AgentIndividualForm(ModelForm):
    main_importer = ModelChoiceField(
        queryset=Importer.objects.none(), label="Importer", disabled=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        importer = Importer.objects.filter(pk=self.initial["main_importer"])
        self.fields["main_importer"].queryset = importer
        self.fields["main_importer"].required = True
        self.fields["user"].required = True

    class Meta(ImporterIndividualForm.Meta):
        fields = ["main_importer", "user", "comments"]
        widgets = {"user": PersonWidget}

    def clean(self):
        self.instance.type = Importer.INDIVIDUAL
        return super().clean()


class AgentOrganisationForm(ModelForm):
    main_importer = ModelChoiceField(
        queryset=Importer.objects.none(), label="Importer", disabled=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        importer = Importer.objects.filter(pk=self.initial["main_importer"])
        self.fields["main_importer"].queryset = importer
        self.fields["main_importer"].required = True
        self.fields["name"].required = True

    class Meta(ImporterOrganisationForm.Meta):
        fields = [
            "main_importer",
            "name",
            "registered_number",
            "comments",
        ]

    def clean(self):
        self.instance.type = Importer.ORGANISATION
        return super().clean()
