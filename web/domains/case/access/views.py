from django.views.generic import TemplateView
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from viewflow import flow
from viewflow.base import Flow, this
from viewflow.flow.views import (
    StartFlowMixin,
)

from django.urls import reverse
from web.views import home
from .forms import AccessRequestForm
from .models import AccessRequestProcess


class AccessRequestCreateView(StartFlowMixin, FormView):
    template_name = 'web/request-access.html'
    form_class = AccessRequestForm

    def get_success_url(self):
        return reverse('request-access')

    def form_valid(self, form):
        access_request = form.save()
        self.activation.process.access_request = access_request
        return super().form_valid(form)


class AccessRequestCreatedView(TemplateView):
    template_name = 'web/request-access-success.html'


# @require_registered
# @flow_start_view
# def request_access(request):
#     request.activation.prepare(request.POST or None, user=request.user)
#     form = AccessRequestForm(request.POST or None)
#     if form.is_valid():
#         access_request = form.instance
#         access_request.user = request.user
#         access_request.save()
#         request.activation.process.access_request = access_request
#         request.activation.done()
#         return render(request, 'web/request-access-success.html')
#
#     return render(request, 'web/request-access.html', {
#         'form': form,
#         'activation': request.activation
#     })


# class AccessRequestFlow(Flow):
#     process_class = AccessRequestProcess
#     request = flow.Start(request_access).Next(flow.End())
#     # request = flow.Start(request_access).Next(this.approve)
#     # approve = flow.View(home).Next(flow.End())
