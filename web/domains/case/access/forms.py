from django.core.exceptions import ValidationError
from django.forms.widgets import Select, Textarea

from web.forms import ViewFlowModelEditForm
from .models import AccessRequest


class AccessRequestForm(ViewFlowModelEditForm):

    def clean(self):
        request_type = self.data['request_type']
        if request_type == AccessRequest.IMPORTER:
            if self.data['request_reason'] == '':
                self.add_error('request_reason',
                               'You must enter this item')
        elif request_type == AccessRequest.IMPORTER_AGENT:
            if self.data['request_reason'] == '':
                self.add_error('request_reason',
                               'You must enter this item')
            if self.data['agent_name'] == '':
                self.add_error('agent_name',
                               'You must enter this item')
            if self.data['agent_address'] == '':
                self.add_error('agent_address',
                               'You must enter this item')
        elif request_type == AccessRequest.EXPORTER:
            pass
        elif request_type == AccessRequest.EXPORTER_AGENT:
            if self.data['agent_name'] == '':
                self.add_error('agent_name',
                               'You must enter this item')
            if self.data['agent_address'] == '':
                self.add_error('agent_address',
                               'You must enter this item')
        else:
            raise ValidationError("Unknown access request type")

    class Meta:
        model = AccessRequest

        fields = [
            'request_type', 'organisation_name', 'organisation_address',
            'request_reason', 'agent_name', 'agent_address',
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


class ReviewAccessRequestForm(ViewFlowModelEditForm):
    class Meta:
        model = AccessRequest

        fields = [
            'response'
        ]
