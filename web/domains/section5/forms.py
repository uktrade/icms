from django import forms
from django_select2.forms import Select2MultipleWidget

from web.domains.office.models import Office
from web.domains.section5.models import ClauseQuantity, Section5Authority, Section5Clause


class Section5AuthorityForm(forms.ModelForm):
    postcode = forms.CharField()
    files = forms.FileField(
        required=False,
        label="Documents",
        widget=forms.widgets.ClearableFileInput(
            attrs={"multiple": True, "onchange": "updateList()"}
        ),
    )
    linked_offices = forms.ModelMultipleChoiceField(
        label="Linked Offices",
        queryset=Office.objects.none(),
        widget=Select2MultipleWidget,
        required=False,
        help_text="""
            The offices the applicant may use this authority with. If no offices are linked,
            the applicant may use this authority with any office they select.
        """,
    )
    start_date = forms.DateField(label="Start Date", widget=forms.DateInput)
    end_date = forms.DateField(
        label="End Date",
        widget=forms.DateInput,
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
            "address": forms.Textarea({"rows": 3}),
            "further_details": forms.Textarea({"rows": 3}),
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


class Section5ClauseForm(forms.ModelForm):
    class Meta:
        model = Section5Clause
        fields = ("clause", "description")


class ClauseQuantityForm(forms.ModelForm):
    section5clause = forms.ModelChoiceField(queryset=Section5Clause.objects.filter(is_active=True))

    class Meta:
        model = ClauseQuantity
        fields = ("section5clause", "quantity", "infinity")
        labels = {"infinity": "Unlimited"}
        widgets = {"quantity": forms.TextInput(attrs={"placeholder": "Quantity"})}

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
