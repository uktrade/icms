from django import forms
from web.forms import ModelDisplayForm, ModelEditForm
from web.domains.case.models import FurtherInformationRequest


class FurtherInformationRequestForm(ModelEditForm):

    def get_top_buttons(self):
        """
        buttons to show on the form's top row
        """
        return ['save']

    def get_bottom_buttons(self):
        """
        buttons to show on the form's bottom row
        """
        return ['send', 'delete']

    class Meta:
        model = FurtherInformationRequest
        fields = ['status', 'request_subject', 'email_cc_address_list', 'request_detail', 'files']
        labels = {
            'email_cc_address_list': 'Request CC Email Addresses',
            'files': 'Documents',
            'requested_datetime': 'Request Date',
        }

        help_texts = {
               'email_cc_address_list': """
                You may enter a list of email addresses to CC this email to.
                <br>
                Use a semicolon (<strong>;</strong>) to seperate multiple addresses.
                <br>
                <br>
                E.g. <span style="white-space:nowrap;">john@smith.com <strong>;</strong> jane@smith.com</span>"""
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

    def get_top_buttons(self):
        """
        buttons to show on the form's top row
        """
        if self.instance.status == FurtherInformationRequest.DRAFT:
            return ['edit']

        return []

    def get_bottom_buttons(self):
        """
        buttons to show on the form's bottom row
        """
        if self.instance.status == FurtherInformationRequest.OPEN:
            return ['withdraw']

        return []

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
