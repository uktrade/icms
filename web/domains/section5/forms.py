from django import forms
from django_select2.forms import Select2MultipleWidget

from web.domains.file.utils import MultipleFileField
from web.forms.fields import JqueryDateField
from web.models import ClauseQuantity, Office, Section5Authority, Section5Clause


class Section5AuthorityForm(forms.ModelForm):
    postcode = forms.CharField()

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
    start_date = JqueryDateField(label="Start Date")
    end_date = JqueryDateField(
        label="End Date",
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
        )
        widgets = {
            "address": forms.Textarea({"rows": 3}),
            "further_details": forms.Textarea({"rows": 3}),
        }

    def __init__(self, importer, *args, can_upload_files=False, **kwargs):
        super().__init__(*args, **kwargs)
        if can_upload_files:
            # Add file field
            self.fields["documents"] = MultipleFileField(
                show_default_help_text=False, required=False
            )
        self.importer = importer
        self.fields["linked_offices"].queryset = self.importer.offices.filter(is_active=True)

    def clean(self):
        data = super().clean()

        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and (data["start_date"] > data["end_date"]):
            self.add_error("end_date", "End Date must be after Start Date.")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.importer = self.importer
        if commit:
            instance.save()
            self.save_m2m()
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
