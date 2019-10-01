from django.shortcuts import render
from viewflow import flow
from viewflow.base import Flow, this
from viewflow.decorators import flow_start_view
from web.auth.decorators import require_registered

from .forms import AccessRequestForm
from .models import AccessRequestProcess
from web.views import home


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
