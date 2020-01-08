from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views import generic
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from viewflow.decorators import flow_view
from viewflow.flow.views import (
    StartFlowMixin,
    FlowMixin,
)

from .forms import AccessRequestForm, ReviewAccessRequestForm, AccessRequest


class AccessRequestCreateView(StartFlowMixin, FormView):
    template_name = 'web/request-access.html'
    form_class = AccessRequestForm

    def get_success_url(self):
        return reverse('access_request_created')

    def form_valid(self, form):
        access_request = form.save(commit=False)
        access_request.submitted_by = self.request.user
        access_request.save()

        self.activation.process.access_request = access_request
        return super().form_valid(form)


class AccessRequestCreatedView(TemplateView):
    template_name = 'web/request-access-success.html'


class ILBReviewRequest(FlowMixin, generic.UpdateView):
    template_name = 'web/review-access-request.html'
    model = AccessRequest

    form_class = ReviewAccessRequestForm

    def get_object(self):
        return self.activation.process

    def request_details(self):
        return self.activation.process.access_request

    def form_valid(self, form):
        form.save()
        self.activation_done()
        return redirect(self.get_success_url())


@flow_view
def registraton_view(request, activation):
    activation.prepare(request.POST or None, user=request.user)
    form = AccessRequestForm(request.POST or None)

    if form.is_valid():
        activation.process.user = form.save()
        activation.done()
        return redirect(...)

    return render(request, 'web/access-approved.html', {
        'form': form,
        'activation': activation,
    })


class AccessApproved(FlowMixin, FormView):
    template_name = 'web/access-approved.html'
    form_class = AccessRequestForm

    def form_valid(self, form):
        access_request = form.save()
        self.activation_done()
        return redirect(self.get_success_url())


class AccessRefused(FlowMixin, FormView):
    template_name = 'web/access-refused.html'
    form_class = AccessRequestForm

    def form_valid(self, form):
        access_request = form.save()
        self.activation_done()
        return redirect(self.get_success_url())

# WIP:
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
