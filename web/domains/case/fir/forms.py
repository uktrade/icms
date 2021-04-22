import structlog as logging
from django.core.validators import validate_email
from django.forms import ChoiceField, ClearableFileInput, FileField, ModelForm, Textarea

from web.domains.case.fir.models import FurtherInformationRequest

logger = logging.getLogger(__name__)


class FurtherInformationRequestForm(ModelForm):
    status = ChoiceField(choices=FurtherInformationRequest.STATUSES, disabled=True)

    # TODO: change UI to use single-file uploads and use ICMSFileField
    files = FileField(
        required=False,
        label="Upload New Documents",
        widget=ClearableFileInput(attrs={"multiple": True, "onchange": "updateList()"}),
    )

    class Meta:
        model = FurtherInformationRequest
        fields = ["status", "request_subject", "email_cc_address_list", "request_detail", "files"]
        labels = {
            "email_cc_address_list": "Request CC Email Addresses",
            "requested_datetime": "Request Date",
        }

        help_texts = {
            "email_cc_address_list": """
                You may enter a list of email addresses to CC this email to.
                <br>
                Use a semicolon (<strong>;</strong>) to seperate multiple addresses.
                <br>
                E.g. <span style="white-space:nowrap;">john@smith.com <strong>;</strong> \
                jane@smith.com</span>"""
        }

    def clean_email_cc_address_list(self):
        """Validate ';' splitted email address list"""
        email_cc_address_list = self.cleaned_data.get("email_cc_address_list")
        if email_cc_address_list:
            for email in email_cc_address_list.split(";"):
                email = email.strip()
                validate_email(email)
        return email_cc_address_list

    def clean(self):
        data = super().clean()
        data.pop("files", None)
        return data


class FurtherInformationRequestResponseForm(ModelForm):
    # TODO: change UI to use single-file uploads and use ICMSFileField
    files = FileField(
        required=False,
        label="Upload New Documents",
        widget=ClearableFileInput(attrs={"multiple": True, "onchange": "updateList()"}),
    )

    class Meta:
        model = FurtherInformationRequest
        fields = ["response_detail", "files"]
        labels = {"response_detail": "Response Details"}
        widgets = {"response_detail": Textarea({"rows": 5})}

    def clean(self):
        data = super().clean()
        data.pop("files", None)
        return data
