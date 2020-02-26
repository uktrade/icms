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


class AccessRequestFirView(PostActionMixin):
    """
    Access Request Further Information Request

    This view class handles all actions that can be performed on a FIR
    """
    template_name = 'web/access-request/access-request-fir-list.html'
    FIR_TEMPLATE_CODE = 'IAR_RFI_EMAIL'

    def get(self, request, process_id):
        """
        Lists all FIRs associated to the acces request

        Params:
            process_id - Access Request id
        """
        return render(
            request,
            self.template_name,
            self.get_context_data(process_id)
        )

    def edit(self, request, process_id, *args, **kwargs):
        """
        Edits the FIR selected by the user.
        The selected FIR comes from the id property in the request body

        Params:
            process_id - Access Request id
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

    def set_fir_status(self, id, status):
        """
        Helper function to set and save a FIR status

        returns the changed FIR
        """
        model = FurtherInformationRequest.objects.get(pk=id)
        model.status = status
        model.save()

        return model

    def withdraw(self, request, process_id):
        """
        Marks the FIR as withdrawn

        Params:
            process_id - Access Request id
        """
        self.set_fir_status(request.POST['id'], FurtherInformationRequest.CLOSED)
        return redirect('access_request_fir_list', process_id=process_id)

    def delete(self, request, process_id):
        """
        Marks the FIR as deleted and sets it as inactive

        Params:
            process_id - Access Request id
        """
        model = self.set_fir_status(request.POST['id'], FurtherInformationRequest.DELETED)
        model.is_active = False
        model.save()

        return redirect('access_request_fir_list', process_id=process_id)

    def save(self, request, process_id, *args, **kwargs):
        """
        Saves the FIR being editted by the user

        Params:
            process_id - Access Request id
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

    def new(self, request, process_id):
        """
        Creates a new FIR and associates it with the current access request then display the FIR form
        so the user can edit data

        Params:
            process_id - Access Request id
        """
        access_request = AccessRequest.objects.get(pk=process_id)
        try:
            template = Template.objects.get(template_code=self.FIR_TEMPLATE_CODE, is_active=True)
        except Exception as e:
            logger.warn('could not fetch templat with code "%s" - reason %s' % (self.FIR_TEMPLATE_CODE, str(e)))
            template = Template()

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
        """
        Helper function to generate context data to be sent to views

        Params:
            process_id - Access Request id
            selected_fir - id of the FIR the user is editing (or None)
            form - the form the user has submitted (or None, if present the form is returned instead of creating a new one)
        """
        process = AccessRequestProcess.objects.get(pk=process_id)
        items = process.access_request.further_information_requests.all().order_by('pk').reverse()

        return {
            'fir_list': [self.create_display_or_edit_form(fir, selected_fir, form) for fir in items],
            'activation': {  # keeping the same format as viewflow, so sidebar works seamlessly
                'process': process,
            }
        }
