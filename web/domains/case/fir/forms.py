import structlog as logging
from django.core.validators import validate_email
from django.forms import ModelForm
from django.forms.widgets import Textarea
from django.utils import timezone

from web.domains.case.fir.models import FurtherInformationRequest

logger = logging.getLogger(__name__)


class FurtherInformationRequestForm(ModelForm):
    """Request form for FIRs.
       Takes an optional user keyword arg to set fir requested by"""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def _is_draft(self):
        """Check submitted data to determine if saving as draft"""
        return "_save_draft" in self.data

    def save(self, commit=True):
        """Set request status/date before save"""
        # TODO: Skip form validations if saving as draft?
        fir = super().save(commit=False)
        fir.requested_by = self.user
        if not self._is_draft():
            fir.status = FurtherInformationRequest.OPEN

        if commit:
            fir.save()

        return fir

    def clean_email_cc_address_list(self):
        """Validate ';' splitted email address list"""
        email_cc_address_list = self.cleaned_data.get("email_cc_address_list")
        if email_cc_address_list:
            for email in email_cc_address_list.split(";"):
                email = email.strip()
                validate_email(email)
        return email_cc_address_list

    class Meta:
        model = FurtherInformationRequest
        fields = ["request_subject", "email_cc_address_list", "request_detail"]
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
                <br>
                E.g. <span style="white-space:nowrap;">john@smith.com <strong>;</strong> \
                jane@smith.com</span>"""
        }


class FurtherInformationRequestResponseForm(ModelForm):
    def __init__(self, response_by, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_by = response_by

    def save(self, commit=True):
        """Set response status/date before save"""
        fir = super().save(commit=False)
        fir.response_datetime = timezone.now()
        fir.status = FurtherInformationRequest.RESPONDED
        fir.response_by = self.response_by
        if commit:
            fir.save()
        return fir

    class Meta:
        model = FurtherInformationRequest
        fields = [
            "response_detail",
        ]
        labels = {
            "response_detail": "Response Details",
        }
        widgets = {
            "response_detail": Textarea({"rows": 5}),
        }
