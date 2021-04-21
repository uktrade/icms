from django import forms
from django.core.exceptions import ValidationError
from django_select2 import forms as s2forms
from guardian.shortcuts import get_users_with_perms

from web.domains.country.models import Country
from web.domains.file.models import File
from web.domains.sanction_email.models import SanctionEmail
from web.domains.user.models import User

from . import widgets
from .models import (
    SanctionEmailMessage,
    SanctionsAndAdhocApplication,
    SanctionsAndAdhocApplicationGoods,
)


class SanctionsAndAdhocLicenseForm(forms.ModelForm):
    contact = forms.ModelChoiceField(
        queryset=User.objects.none(),
        help_text="Select the main point of contact for the case. This will usually be the person who created the application.",
    )

    applicant_reference = forms.CharField(
        label="Applicant's Reference",
        help_text="Enter your own reference for this application.",
        required=False,
    )
    origin_country = forms.ModelChoiceField(
        label="Country Of Origin",
        queryset=Country.objects.filter(country_groups__name="Sanctions and Adhoc License"),
    )

    consignment_country = forms.ModelChoiceField(
        label="Country Of Consignment",
        queryset=Country.objects.filter(country_groups__name="Sanctions and Adhoc License"),
    )
    exporter_name = forms.CharField(
        label="Exporter Name",
        required=False,
    )
    exporter_address = forms.CharField(
        label="Exporter Address",
        required=False,
    )

    class Meta:
        model = SanctionsAndAdhocApplication
        fields = (
            "contact",
            "applicant_reference",
            "origin_country",
            "consignment_country",
            "exporter_name",
            "exporter_address",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = get_users_with_perms(
            self.instance.importer, only_with_perms_in=["is_contact_of_importer"]
        )
        self.fields["contact"].queryset = users.filter(is_active=True)


class GoodsForm(forms.ModelForm):
    class Meta:
        # TODO restrict commodities to group when it becomes known
        model = SanctionsAndAdhocApplicationGoods
        fields = ["commodity_code", "goods_description", "quantity_amount", "value"]
        widgets = {
            "goods_description": forms.Textarea(attrs={"cols": 80, "rows": 20}),
        }
        labels = {"value": "Value (GBP CIF)"}


class SupportingDocumentForm(forms.Form):
    document = forms.FileField(required=True, widget=forms.ClearableFileInput())


class SubmitSanctionsForm(forms.Form):
    confirmation = forms.CharField(
        label='Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    )

    def clean_confirmation(self):
        confirmation = self.cleaned_data["confirmation"]

        if confirmation != "I AGREE":
            raise ValidationError("Please agree to the declaration of truth.")

        return confirmation


class SanctionEmailMessageForm(forms.ModelForm):
    status = forms.CharField(widget=forms.TextInput(attrs={"readonly": "readonly"}))
    to = forms.ChoiceField(label="To", widget=s2forms.Select2Widget, choices=())
    cc_address_list = forms.CharField(
        required=False, label="Cc", help_text="Enter CC email addresses separated by a comma"
    )
    attachments = forms.ModelMultipleChoiceField(
        required=False,
        widget=widgets.CheckboxSelectMultipleTable(attrs={"class": "radio-relative"}),
        queryset=File.objects.none(),
    )
    subject = forms.CharField(label="Subject")
    body = forms.CharField(label="Body", widget=forms.Textarea)

    class Meta:
        model = SanctionEmailMessage
        fields = (
            "status",
            "to",
            "cc_address_list",
            "attachments",
            "subject",
            "body",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [
            (c.email, f"{c.name} ({c.email})") for c in SanctionEmail.objects.filter(is_active=True)
        ]
        self.fields["to"].choices = choices

        files = self.instance.application.supporting_documents.filter(is_active=True)
        self.fields["attachments"].queryset = files
        # set files and process on the widget to make them available in the widget's template
        self.fields["attachments"].widget.qs = files
        self.fields["attachments"].widget.process = self.instance.application


class SanctionEmailMessageResponseForm(forms.ModelForm):
    class Meta:
        model = SanctionEmailMessage
        fields = ("response",)
