from django.db import transaction
from django.urls import reverse_lazy

from web.auth import utils as auth_utils
from web.views import (ModelCreateView, ModelDetailView, ModelFilterView,
                       ModelUpdateView)
from web.views.actions import Archive, Edit, Unarchive

from .forms import ExporterEditForm, ExporterFilter
from .models import Exporter
from .roles import EXPORTER_ROLES

permissions = 'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'


class ExporterListView(ModelFilterView):
    template_name = 'web/domains/exporter/list.html'
    filterset_class = ExporterFilter
    model = Exporter
    permission_required = permissions
    page_title = 'Maintain Exporters'

    class Display:
        fields = ['name']
        fields_config = {'name': {'header': 'Exporter Name'}}
        actions = [Archive(), Unarchive(), Edit()]


class ExporterEditView(ModelUpdateView):
    template_name = 'web/domains/exporter/edit.html'
    form_class = ExporterEditForm
    success_url = reverse_lazy('exporter-list')
    cancel_url = success_url
    model = Exporter
    permission_required = permissions


class ExporterCreateView(ModelCreateView):
    template_name = 'web/domains/exporter/create.html'
    form_class = ExporterEditForm
    success_url = reverse_lazy('exporter-list')
    cancel_url = success_url
    model = Exporter
    permission_required = permissions
    page_title = 'Create Exporter'

    @transaction.atomic
    def form_valid(self, form):
        """
            Create new exporter roles and permissions with new exporter
        """
        response = super().form_valid(form)
        auth_utils.create_team_roles(self.object, EXPORTER_ROLES)
        return response


class ExporterDetailView(ModelDetailView):
    template_name = 'web/domains/exporter/view.html'
    form_class = ExporterEditForm
    cancel_url = reverse_lazy('exporter-list')
    model = Exporter
    permission_required = permissions
