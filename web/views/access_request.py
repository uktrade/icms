from django.shortcuts import render
from viewflow.decorators import flow_start_view
from viewflow import flow
from viewflow.base import this, Flow
from web.auth.decorators import require_registered
from web.base.forms import ModelForm
from web.base.forms.widgets import (Select, Textarea)
from web.models import AccessRequest, AccessRequestProcess
from .views import home


class AccessRequestForm(ModelForm):
    class Meta:
        model = AccessRequest

        fields = [
            'request_type', 'organisation_name', 'organisation_address',
            'description', 'agent_name', 'agent_address'
        ]

        labels = {
            'request_type':
            'Access Request Type',
            'description':
            'What are you importing and where are you importing it from?'
        }

        widgets = {
            'request_type': Select(choices=AccessRequest.REQUEST_TYPES),
            'organisation_address': Textarea({'rows': 5}),
            'description': Textarea({'rows': 5}),
            'agent_address': Textarea({'rows': 5})
        }


@require_registered
@flow_start_view
def request_access(request):
    request.activation.prepare(request.POST or None, user=request.user)
    form = AccessRequestForm(request.POST or None)
    if form.is_valid():
        access_request = form.instance
        access_request.user = request.user
        access_request.save()
        request.activation.process.access_request = access_request
        request.activation.done()
        return render(request, 'web/request-access-success.html')

    return render(request, 'web/request-access.html', {
        'form': form,
        'activation': request.activation
    })


class AccessRequestFlow(Flow):
    process_class = AccessRequestProcess
    request = flow.Start(request_access).Next(this.approve)
    approve = flow.View(home).Next(flow.End())
