from django import forms
from django.conf import settings
from django.db.models import Q
from django_select2 import forms as s2forms

from web.domains.constabulary.models import Constabulary
from web.domains.file.models import File
from web.domains.firearms.widgets import CheckboxSelectMultipleTable

from . import models


class ConstabularyEmailForm(forms.ModelForm):
    status = forms.CharField(widget=forms.TextInput(attrs={"readonly": "readonly"}))
    email_to = forms.ChoiceField(label="To", widget=s2forms.Select2Widget, choices=())
    email_cc_address_list = forms.CharField(
        required=False, label="Cc", help_text="Enter CC email addresses separated by a comma"
    )
    attachments = forms.ModelMultipleChoiceField(
        required=False,
        widget=CheckboxSelectMultipleTable(attrs={"class": "radio-relative"}),
        queryset=File.objects.none(),
    )
    email_subject = forms.CharField(label="Subject")
    email_body = forms.CharField(label="Body", widget=forms.Textarea)

    class Meta:
        model = models.ConstabularyEmail
        fields = (
            "status",
            "email_to",
            "email_cc_address_list",
            "attachments",
            "email_subject",
            "email_body",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [
            (c.email, f"{c.name} ({c.email})") for c in Constabulary.objects.filter(is_active=True)
        ]
        self.fields["email_to"].choices = choices

        initial = [
            (settings.ICMS_FIREARMS_HOMEOFFICE_EMAIL, settings.ICMS_FIREARMS_HOMEOFFICE_EMAIL)
        ]
        self.fields["email_cc_address_list"].choices = initial + choices

        application = self.instance.import_application

        files = File.objects.filter(
            Q(firearmsauthority__verified_certificates__import_application=application)
            | Q(userimportcertificate__import_application=application)
        ).filter(is_active=True)
        self.fields["attachments"].queryset = files
        # set files and process on the widget to make them available in the widget's template
        self.fields["attachments"].widget.qs = files
        self.fields["attachments"].widget.process = application


class ConstabularyEmailResponseForm(forms.ModelForm):
    class Meta:
        model = models.ConstabularyEmail
        fields = ("email_response",)
