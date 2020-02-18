from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from web.utils import SimpleStartFlowMixin, SimpleFlowMixin
from .forms import AccessRequestForm, ReviewAccessRequestForm
from .models import AccessRequest, AccessRequestProcess
from web.domains.case.forms import FurtherInformationRequestDisplayForm


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


class ILBReviewRequest(SimpleFlowMixin, FormView):
    template_name = 'web/review-access-request.html'
    form_class = ReviewAccessRequestForm

    def form_valid(self, form):
        form.save()
        self.activation_done()
        return redirect(reverse('workbasket'))

    def get_form(self):
        return self.form_class(
            instance=self.activation.process.access_request,
            **self.get_form_kwargs(),
        )


class AccessRequestFirListView(TemplateView):
    """
    Access Request Further Information Request - list
    """
    template_name = 'web/access-request/access-request-fir-list.html'

    def get_context_data(self, process_id, *args, **kwargs):
        process = AccessRequestProcess.objects.get(pk=process_id)
        context = super().get_context_data(*args, **kwargs)

        fir_list = []
        for fir in process.access_request.further_information_requests.all().order_by('pk').reverse():
            fir_list.append(FurtherInformationRequestDisplayForm(
                instance=fir,
                initial={
                    'requested_datetime': fir.date_created_formatted().upper(),
                    'requested_by': fir.requested_by
                }))

        context['fir_list'] = fir_list
        context['activation'] = {
            'process': process,
        }

        return context
