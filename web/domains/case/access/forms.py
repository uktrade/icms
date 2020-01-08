from django.forms.widgets import Select, Textarea
from web.forms import ModelEditForm

from .models import AccessRequest


class AccessRequestForm(ModelEditForm):
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

class ReviewAccessRequestForm(ModelEditForm):
    class Meta:
        model = AccessRequest

        fields = [
            # 'request_type', 'organisation_name', 'organisation_address',
            # 'request_reason', 'agent_name', 'agent_address',
            'response'
        ]

