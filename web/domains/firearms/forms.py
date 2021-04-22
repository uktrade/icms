from django.forms import (
    CharField,
    ClearableFileInput,
    DateField,
    FileField,
    ModelChoiceField,
    ModelForm,
    ModelMultipleChoiceField,
    Textarea,
    TextInput,
)
from django.forms.widgets import CheckboxInput
from django_filters import BooleanFilter, CharFilter, ChoiceFilter, FilterSet
from django_select2.forms import Select2MultipleWidget

from web.domains.office.models import Office
from web.forms.widgets import DateInput

from .models import (
    ActQuantity,
    FirearmsAct,
    FirearmsAuthority,
    ObsoleteCalibre,
    ObsoleteCalibreGroup,
)


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


class FirearmsAuthorityForm(ModelForm):
    postcode = CharField()

    # TODO: change UI to use single-file uploads and use ICMSFileField
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
    )

    class Meta:
        model = FirearmsAuthority
        fields = (
            "reference",
            "certificate_type",
            "issuing_constabulary",
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

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.importer = self.importer
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class FirearmsQuantityForm(ModelForm):
    firearmsact = ModelChoiceField(queryset=FirearmsAct.objects.filter(is_active=True))

    class Meta:
        model = ActQuantity
        fields = ("firearmsact", "quantity", "infinity")
        labels = {"infinity": "Unlimited"}
        widgets = {"quantity": TextInput(attrs={"placeholder": "Quantity"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        firearmsact = self.initial.get("firearmsact")
        if firearmsact:
            clauses = FirearmsAct.objects.filter(pk=firearmsact).values_list("pk", "act")
            self.fields["firearmsact"].choices = clauses

    def clean(self):
        data = super().clean()
        if data.get("infinity") and data.get("quantity"):
            self.cleaned_data.pop("quantity")
