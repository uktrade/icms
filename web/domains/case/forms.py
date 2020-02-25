from django import forms
from web.forms import ModelDisplayForm, ModelEditForm
from web.domains.case.models import FurtherInformationRequest


class FurtherInformationRequestForm(ModelEditForm):

    actions_top = ['save']  # buttons to show on the top row of the form
    actions_bottom = ['send', 'delete'] # buttons to show at the end of the form

    class Meta:
        model = FurtherInformationRequest
        fields = ['status', 'request_subject', 'email_cc_address_list', 'request_detail', 'files']
        labels = {
            'email_cc_address_list': 'Request CC Email Addresses',
            'files': 'Documents',
            'requested_datetime': 'Request Date',
        }

        # From action configuration, here we can configure what button appear where on the FIR form, its style and action
        actions = {
            'save': {
                'css': 'icon-floppy-disk',  # css classes to add (eg: icon classes)
                'action': 'save',           # action name (input field will be created with this value)
                'label': 'Save',            # text to show
            },
            'send': {
                'css': 'primary-button',
                'action': 'send',
                'label': 'Send Request',
            },
            'delete': {
                'css': '',
                'action': 'Delete',
                'label': 'Delete',
            },
            'edit': {
                'css': 'icon-pencil',
                'action': 'edit',
                'label': 'Edit',
            },
            'withdraw': {
                'css': '',
                'action': 'withdraw',
                'label': 'Withdraw Request',
            },
        }


class FurtherInformationRequestDisplayForm(FurtherInformationRequestForm, ModelDisplayForm):

    requested_datetime = forms.CharField(
        label=FurtherInformationRequestForm.Meta.labels['requested_datetime']
    )
    requested_by = forms.CharField()

    actions_top = ['edit']
    actions_bottom = ['withdraw']

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
