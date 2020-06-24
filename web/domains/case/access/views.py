import structlog as logging
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from viewflow.flow.views import (FlowMixin, UpdateProcessView)

from web.domains.exporter.views import ExporterListView
from web.domains.importer.views import ImporterListView
from web.viewflow.mixins import SimpleStartFlowMixin

from . import forms
from .actions import LinkExporter, LinkImporter
from .models import AccessRequest

logger = logging.get_logger(__name__)


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
    template_name = 'web/domains/case/access/request-access.html'
    form_class = forms.AccessRequestForm

    def get_success_url(self):
        return reverse('access:requested')

    def form_valid(self, form):
        access_request = form.save(commit=False)
        access_request.submitted_by = self.request.user
        clean_extra_request_data(access_request)
        access_request.save()

        self.activation.process.access_request = access_request
        return super().form_valid(form)


class AccessRequestCreatedView(TemplateView):
    template_name = 'web/domains/case/access/request-access-success.html'


class AccessRequestReviewView(UpdateProcessView):
    template_name = 'web/domains/case/access/review.html'

    def post(self, request, *args, **kwargs):
        process = self.activation.process
        if 'start_approval' in request.POST:
            process.approval_required = True
        process.save()
        return super().post(request, *args, **kwargs)


class LinkImporterView(FlowMixin, ImporterListView):
    """
        Displays importer list view for searching and linking
        importers to access requests.
    """
    template_name = 'web/domains/case/access/link-importer.html'

    def get_page_title(self):
        return f'{self.activation.process} - {self.activation.flow_task}'

    class Display(ImporterListView.Display):
        actions = [LinkImporter()]


class LinkExporterView(FlowMixin, ExporterListView):
    """
        Displays exporter list view for searching and linking
        exporter to access requests.
    """
    template_name = 'web/domains/case/access/link-exporter.html'

    class Display(ExporterListView.Display):
        actions = [LinkExporter()]


class CloseAccessRequestView(UpdateProcessView):
    template_name = 'web/domains/case/access/close.html'
    form_class = forms.CloseAccessRequestForm

    def get_success_url(self):
        return reverse('workbasket')
