import structlog as logging
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from viewflow.flow.views import FlowMixin, UpdateProcessView

from web.domains.exporter.views import ExporterListView
from web.domains.importer.views import ImporterListView
from web.viewflow.mixins import SimpleStartFlowMixin
from web.views import ModelCreateView

from . import forms
from .actions import LinkExporter, LinkImporter
from .approval.models import ApprovalRequest
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


class RequestApprovalView(FlowMixin, ModelCreateView):
    template_name = 'web/domains/case/access/request-approval.html'
    permission_required = []
    model = ApprovalRequest

    def get_form(self):
        access_request = self.activation.process.access_request
        team = access_request.linked_importer or access_request.linked_exporter
        return forms.ApprovalRequestForm(team, data=self.request.POST or None)

    def form_valid(self, form):
        """
            Save approval request
        """
        process = self.activation.process
        process.save()
        access_request = process.access_request
        approval_request = form.instance
        approval_request.access_request = access_request
        approval_request.requested_by = self.request.user
        return super().form_valid(form)

    def _re_link(self):
        process = self.activation.process
        process.re_link = True
        process.save()
        self.activation.done()
        return redirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        if '_re_link' in request.POST:
            return self._re_link()
        return super().post(request, *args, **kwargs)


class ApprovalRequestReviewView(UpdateProcessView):
    template_name = 'web/domains/case/access/review-approval.html'

    def get_approval_process(self):
        """
            Retrieves the approval process to be reviewed
        """
        process = self.activation.process
        flow_class = self.activation.flow_class
        flow_task = flow_class.approval
        approval_task = flow_class.task_class._default_manager.filter(
            process=process, flow_task=flow_task).order_by('-created').first()
        return approval_task.activate().subprocesses().first()

    def get_context_data(self, *args, **kwargs):
        """
            Adds latest approval process into context
        """
        context = super().get_context_data(*args, **kwargs)
        context['approval_process'] = self.get_approval_process()
        return context

    def post(self, request, *args, **kwargs):
        process = self.activation.process
        if 'start_approval' in request.POST:
            process.restart_approval = True
        process.save()
        return super().post(request, *args, **kwargs)
