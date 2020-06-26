from django.core.exceptions import ValidationError
from django.forms.widgets import Select, Textarea

from web.forms import ViewFlowForm, ModelEditForm

from .models import AccessRequest


class AccessRequestForm(ViewFlowForm, ModelEditForm):
    def validate_fields(self, fields, cleaned_data):
        for field in fields:
            if cleaned_data[field] == '':
                self.add_error(field, 'You must enter this item')

    def clean(self):
        cleaned_data = super().clean()
        request_type = cleaned_data['request_type']
        if request_type == AccessRequest.IMPORTER:
            self.validate_fields(['request_reason'], cleaned_data)
        elif request_type == AccessRequest.IMPORTER_AGENT:
            self.validate_fields(
                ['request_reason', 'agent_name', 'agent_address'],
                cleaned_data)
        elif request_type == AccessRequest.EXPORTER:
            pass
        elif request_type == AccessRequest.EXPORTER_AGENT:
            self.validate_fields(['agent_name', 'agent_address'], cleaned_data)
        else:
            raise ValidationError("Unknown access request type")

    class Meta:
        model = AccessRequest

        fields = [
            'request_type',
            'organisation_name',
            'organisation_address',
            'request_reason',
            'agent_name',
            'agent_address',
        ]

        labels = {
            'request_type':
            'Access Request Type',
            'request_reason':
            'What are you importing and where are you importing it from?'
        }

        widgets = {
            'request_type': Select(choices=AccessRequest.REQUEST_TYPES),
            'organisation_address': Textarea({'rows': 5}),
            'request_reason': Textarea({'rows': 5}),
            'agent_address': Textarea({'rows': 5}),
        }

        config = {
            '__all__': {
                'label': {
                    'cols': 'four'
                },
                'input': {
                    'cols': 'four'
                },
                'padding': {
                    'right': 'four'
                }
            }
        }


class CloseAccessRequestForm(ModelEditForm):
    class Meta:
        model = AccessRequest

        fields = ['response', 'response_reason']
