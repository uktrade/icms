import structlog as logging
from django.forms import ChoiceField, ModelForm, Textarea

from web.models import FurtherInformationRequest

logger = logging.getLogger(__name__)


class FurtherInformationRequestForm(ModelForm):
    status = ChoiceField(choices=FurtherInformationRequest.STATUSES, disabled=True)

    class Meta:
        model = FurtherInformationRequest
        fields = ("status", "request_subject", "email_cc_address_list", "request_detail")


class FurtherInformationRequestResponseForm(ModelForm):
    class Meta:
        model = FurtherInformationRequest
        fields = ("response_detail",)
        widgets = {"response_detail": Textarea({"rows": 5})}
