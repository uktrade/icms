from django.forms import (
    CharField,
    ClearableFileInput,
    DateField,
    FileField,
    ModelChoiceField,
    ModelForm,
    ModelMultipleChoiceField,
)
from django.forms.widgets import CheckboxInput, Textarea, TextInput
from django_filters import BooleanFilter, CharFilter, ChoiceFilter, FilterSet
from django_select2.forms import Select2MultipleWidget

from web.domains.firearms.models import ClauseQuantity
from web.domains.office.models import Office
from web.domains.section5.models import Section5Clause
from web.forms.widgets import DateInput

from .models import ObsoleteCalibre, ObsoleteCalibreGroup, Section5Authority


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


class Section5AuthorityForm(ModelForm):
    postcode = CharField()
    files = FileField(
        required=False,
        label="Documents",
        widget=ClearableFileInput(attrs={"multiple": True, "onchange": "updateList()"}),
    )
    linked_offices = ModelMultipleChoiceField(
        label="Linked Offices",
        queryset=Office.objects.none(),
        widget=Select2MultipleWidget,
        required=False,
        help_text="""
            The offices the applicant may use this authority with. If no offices are linked,
            the applicant may use this authority with any office they select.
        """,
    )
    start_date = DateField(label="Start Date", widget=DateInput)
    end_date = DateField(
        label="End Date",
        widget=DateInput,
        help_text="A user will not be able to use this verified Authority on an application past this date.",
    )

    class Meta:
        model = Section5Authority
        fields = (
            "reference",
            "postcode",
            "address",
            "linked_offices",
            "start_date",
            "end_date",
            "further_details",
            "files",
        )
        widgets = {
            "address": Textarea({"rows": 3}),
            "further_details": Textarea({"rows": 3}),
        }

    def __init__(self, importer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.importer = importer
        self.fields["linked_offices"].queryset = self.importer.offices.all()

    def clean(self):
        data = super().clean()
        # files handled in the view
        data.pop("files", None)

        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if start_date and end_date and data["start_date"] > data["end_date"]:
            self.add_error("end_date", "End Date must be after Start Date.")
        return data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.importer = self.importer
        if commit:
            instance.save()
        return instance


class ClauseQuantityForm(ModelForm):
    section5clause = ModelChoiceField(queryset=Section5Clause.objects.filter(is_active=True))

    class Meta:
        model = ClauseQuantity
        fields = ("section5clause", "quantity", "infinity")
        labels = {"infinity": "Unlimited"}
        widgets = {"quantity": TextInput(attrs={"placeholder": "Quantity"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        section5clause = self.initial.get("section5clause")
        if section5clause:
            clauses = Section5Clause.objects.filter(pk=section5clause).values_list("pk", "clause")
            self.fields["section5clause"].choices = clauses

    def clean(self):
        data = super().clean()
        if data.get("infinity") and data.get("quantity"):
            self.cleaned_data.pop("quantity")
