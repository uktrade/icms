from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from viewflow.flow.views.start import BaseStartFlowMixin
from viewflow.flow.views.task import BaseFlowMixin

from .forms import AccessRequestForm, ReviewAccessRequestForm
from .models import AccessRequest


def clean_extra_request_data(access_request):
    if access_request.request_type == AccessRequest.IMPORTER:
        access_request.agent_name = None
        access_request.agent_address = None
    elif access_request.request_type == AccessRequest.IMPORTER_AGENT:
        pass
    elif access_request.request_type == AccessRequest.EXPORTER:
        access_request.agent_name = None
        access_request.agent_address = None
        access_request.request_reason = None
    elif access_request.request_type == AccessRequest.EXPORTER_AGENT:
        access_request.request_reason = None
    else:
        raise ValueError("Unknown access request type")


class SimpleStartFlowMixin(BaseStartFlowMixin):
    """StartFlowMixin without MessageUserMixin"""

    def activation_done(self, *args, **kwargs):
        """Finish task activation."""
        self.activation.done()

    def form_valid(self, *args, **kwargs):
        """If the form is valid, save the associated model and finish the task."""
        super(SimpleStartFlowMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        return HttpResponseRedirect(self.get_success_url())


class AccessRequestCreateView(SimpleStartFlowMixin, FormView):
    template_name = 'web/request-access.html'
    form_class = AccessRequestForm

    def get_success_url(self):
        return reverse('access_request_created')

    def form_valid(self, form):
        access_request = form.save(commit=False)
        access_request.submitted_by = self.request.user
        clean_extra_request_data(access_request)
        access_request.save()

        self.activation.process.access_request = access_request
        return super().form_valid(form)


class AccessRequestCreatedView(TemplateView):
    template_name = 'web/request-access-success.html'


class SimpleFlowMixin(BaseFlowMixin):
    """FlowMixin without MessageUserMixin."""

    def activation_done(self, *args, **kwargs):
        """Finish the task activation."""
        self.activation.done()

    def form_valid(self, *args, **kwargs):
        """If the form is valid, save the associated model and finish the task."""
        super(SimpleFlowMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        return HttpResponseRedirect(self.get_success_url())


class ILBReviewRequest(SimpleFlowMixin, FormView):
    template_name = 'web/review-access-request.html'
    form_class = ReviewAccessRequestForm

    def request_details(self):
        return self.activation.process.access_request

    def form_valid(self, form):
        form.save()
        self.activation_done()
        return redirect(reverse('workbasket'))

    def get_form(self):
        return self.form_class(
            instance=self.activation.process.access_request,
            **self.get_form_kwargs(),
        )
