from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.http import HttpResponseBadRequest
from django.shortcuts import render

from web.utils import SimpleStartFlowMixin, SimpleFlowMixin
from .forms import AccessRequestForm, ReviewAccessRequestForm
from .models import AccessRequest, AccessRequestProcess
from web.domains.case.forms import FurtherInformationRequestDisplayForm, FurtherInformationRequestForm
from web.views.mixins import PostActionMixin


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


class AccessRequestFirListView(TemplateView, PostActionMixin):
    """
    Access Request Further Information Request - list
    """
    template_name = 'web/access-request/access-request-fir-list.html'

    def edit(self, request, process_id, *args, **kwargs):
        """
        Edits the FIR selected by the user.
        The selected FIR comes from the id property in the request body
        """

        data = request.POST if request.POST else None
        if not data or 'id' not in data:
            return HttpResponseBadRequest('Invalid body received')

        fir_id = int(data['id'])

        return render(
            request,
            self.template_name,
            self.get_context_data(process_id, selected_fir=fir_id, action="edit")
        )

    def create_display_or_edit_form(self, fir, selected_fir):
        """
        creates an edit form if fir is the selected fir otherwise creates a display form
        """
        if selected_fir and fir.id == selected_fir:
            return FurtherInformationRequestForm(instance=fir)

        return FurtherInformationRequestDisplayForm(
            instance=fir,
            initial={
                'requested_datetime': fir.date_created_formatted().upper(),
                'requested_by': fir.requested_by
            }
        )

    def get_context_data(self, process_id, selected_fir=None, action="display", *args, **kwargs):
        process = AccessRequestProcess.objects.get(pk=process_id)
        context = super().get_context_data(*args, **kwargs)

        items = process.access_request.further_information_requests.all().order_by('pk').reverse()

        context['fir_list'] = [self.create_display_or_edit_form(fir, selected_fir) for fir in items]
        context['action'] = action
        context['activation'] = {
            'process': process,
        }

        return context
