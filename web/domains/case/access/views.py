from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
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

    #   def get_form(self):
    #   return self.form_class(instance=self.activation.process.access_request, **self.get_form_kwargs())

    def request_details(self):
        return self.activation.process.access_request

    def form_valid(self, form):
        access_request = form.save()

        return redirect(self.get_success_url())


# class ILBReviewRequest(FlowMixin, FormView):
#     template_name = 'web/review-access-request.html'
#     form_class = ReviewAccessRequestForm
#
#     def request_details(self):
#         return self.activation.process.access_request
#
#     def get_form(self):
#         return self.form_class(instance=self.activation.process.access_request, **self.get_form_kwargs())
#
#     def get_success_url(self):
#         test = get_next_task_url(self.request, self.request.activation.process)
#         return redirect(get_next_task_url(self.request, self.request.activation.process))
#
#     def form_valid(self, form):
#         access_request = form.save()
#         return super().form_valid(form)


class AccessApproved(FlowMixin, generic.UpdateView):
    template_name = 'web/access-approved.html'


class AccessRefused(FlowMixin, generic.UpdateView):
    template_name = 'web/access-refused.html'

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
