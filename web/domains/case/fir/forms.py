import logging

from django import forms

from web.models import FurtherInformationRequest

logger = logging.getLogger(__name__)


class FurtherInformationRequestForm(forms.ModelForm):
    status = forms.ChoiceField(choices=FurtherInformationRequest.STATUSES, disabled=True)
    release_ownership = forms.BooleanField(required=False, initial=True, widget=forms.HiddenInput)
    send = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)

    class Meta:
        model = FurtherInformationRequest
        fields = ("status", "request_subject", "request_detail")

    @property
    def media(self):
        if self.instance.accessrequest_set.exists():
            js = ["web/js/pages/edit-fir-access-request.js"]
        else:
            js = ["web/js/pages/edit-fir.js"]

        media = forms.Media(js=js)
        return media


class FurtherInformationRequestResponseForm(forms.ModelForm):
    class Meta:
        model = FurtherInformationRequest
        fields = ("response_detail",)
        widgets = {"response_detail": forms.Textarea({"rows": 5})}
        labels = {"response_detail": "Response Details"}
