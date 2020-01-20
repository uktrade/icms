from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from viewflow.flow.views import (
    StartFlowMixin,
    FlowMixin,
)

from .forms import AccessRequestForm, ReviewAccessRequestForm


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


class ILBReviewRequest(FlowMixin, FormView):
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
