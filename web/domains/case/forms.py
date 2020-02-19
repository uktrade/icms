from django import forms
from web.forms import ModelDisplayForm, ModelEditForm
from web.domains.case.models import FurtherInformationRequest


class FurtherInformationRequestForm(ModelEditForm):
    class Meta:
        model = FurtherInformationRequest
        fields = ['status', 'request_subject', 'email_cc_address_list', 'request_detail', 'files']
        labels = {
            'email_cc_address_list': 'Request CC Email Addresses',
            'files': 'Documents',
            'requested_datetime': 'Request Date',
        }


class FurtherInformationRequestDisplayForm(FurtherInformationRequestForm, ModelDisplayForm):

    requested_datetime = forms.CharField(
        label=FurtherInformationRequestForm.Meta.labels['requested_datetime']
    )
    requested_by = forms.CharField()

    class Meta(FurtherInformationRequestForm.Meta):
        config = {
                'requested_datetime': {
                    'padding': {'right': None},
                    'label': {
                        'cols': 'three'
                    },
                    'input': {
                        'cols': 'two'
                    },
                },
                'requested_by': {
                    'label': {
                        'cols': 'two'
                    },
                    'input': {
                        'cols': 'two'
                    },
                }
        }
