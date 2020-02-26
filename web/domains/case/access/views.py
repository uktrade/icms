from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.http import HttpResponseBadRequest
from django.shortcuts import render
import logging

from web.utils import SimpleStartFlowMixin, SimpleFlowMixin
from .forms import AccessRequestForm, ReviewAccessRequestForm
from .models import AccessRequest, AccessRequestProcess
from web.domains.case.forms import FurtherInformationRequestDisplayForm, FurtherInformationRequestForm
from web.views.mixins import PostActionMixin
from web.domains.case.models import FurtherInformationRequest
from web.domains.template.models import Template

logger = logging.getLogger(__name__)


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
    FIR_TEMPLATE_CODE = 'IAR_RFI_EMAIL'

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
            self.get_context_data(process_id, selected_fir=fir_id)
        )

    def save(self, request, process_id, *args, **kwargs):
        """
        Saves the FIR being editted by the user
        """
        model = FurtherInformationRequest.objects.get(pk=request.POST['id'])
        form = FurtherInformationRequestForm(data=request.POST, instance=model)

        if form.is_valid():
            form.save()
            return redirect('access_request_fir_list', process_id=process_id)

        return render(
            request,
            self.template_name,
            self.get_context_data(process_id, selected_fir=model.id, form=form)
        )

    def _fetchTemplate(self, code):
        """
        Fetches a template from the database, returns an empty template if no template can be found
        """
        try:
            return Template.objects.get(template_code=self.FIR_TEMPLATE_CODE, is_active=True)
        except Exception as e:
            logger.warn(e)
            return Template()

    def new(self, request, process_id):
        """
        Creates a new FIR and associates it with the current access request then display the FIR form
        so the user can edit data
        """
        access_request = AccessRequest.objects.get(pk=process_id)
        template = self._fetchTemplate(self.FIR_TEMPLATE_CODE)

        instance = FurtherInformationRequest()
        instance.requested_by = request.user
        instance.request_detail = template.get_content({
            'CURRENT_USER_NAME': self.request.user.full_name,
            'REQUESTER_NAME': access_request.submitted_by.full_name
        })
        instance.save()

        access_request.further_information_requests.add(instance)

        return render(
            request,
            self.template_name,
            self.get_context_data(process_id, selected_fir=instance.id)
        )

    def create_display_or_edit_form(self, fir, selected_fir, form):
        """
        This function either returns an Further Information Request (FIR) form, or a read only version of it.

        By default returns a read only version of the FIR form (for display puposes).

        If `fir.id` is is the same as `selected_fir` then a "editable" version of the form is returned

        Params:
        fir - FurtherInformationRequest model
        selected_fir - id of the FIR the user is editing (or None)
        form - the form the user has submitted (or None, if present the form is returned instead of creating a new one)
        """
        if selected_fir and fir.id == selected_fir:
            return form if form else FurtherInformationRequestForm(instance=fir)

        return FurtherInformationRequestDisplayForm(
            instance=fir,
            initial={
                'requested_datetime': fir.date_created_formatted().upper(),
                'requested_by': fir.requested_by.full_name
            }
        )

    def get_context_data(self, process_id, selected_fir=None, form=None, *args, **kwargs):
        process = AccessRequestProcess.objects.get(pk=process_id)
        context = super().get_context_data(*args, **kwargs)

        items = process.access_request.further_information_requests.all().order_by('pk').reverse()
        logger.debug('getting context data')
        context['fir_list'] = [self.create_display_or_edit_form(fir, selected_fir, form) for fir in items]
        context['activation'] = {
            'process': process,
        }

        return context
