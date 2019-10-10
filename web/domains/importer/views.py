import logging

from django.shortcuts import render
from django.urls import reverse_lazy
from web.domains.team.mixins import ContactsManagementMixin
from web.views import (ModelCreateView, ModelDetailView, ModelFilterView,
                       ModelUpdateView)

from .forms import ImporterDisplayForm, ImporterEditForm, ImporterFilter
from .models import Importer

logger = logging.getLogger(__name__)


class ImporterListView(ModelFilterView):
    template_name = 'web/importer/list.html'
    filterset_class = ImporterFilter
    model = Importer
    permission_required = \
        'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'

    class Display:
        fields = [('full_name', 'registered_number', 'entity_type')]
        headers = ['Importer Name / Importer Reg No / Importer Entity Type']
        edit = True
        view = True
        archive = True


class ImporterEditView(ContactsManagementMixin, ModelUpdateView):
    template_name = 'web/importer/edit.html'
    form_class = ImporterEditForm
    success_url = reverse_lazy('importer-list')
    model = Importer
    permission_required = \
        'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'

    def get(self, request, pk, importer_id=None):
        form = super().get_form(pk=pk)
        context = {
            'contacts': self._get_initial_data(form.instance),
            'form': form
        }
        if importer_id:
            context['importer'] = Importer.objects.filter(pk=importer_id).get()
        return self._render(context)


class ImporterCreateView(ModelCreateView):
    template_name = 'web/importer/create.html'
    form_class = ImporterEditForm
    success_url = reverse_lazy('importer-list')
    model = Importer
    permission_required = \
        'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'

    def get(self, request, importer_id=None):
        form = super().get_form()
        context = {'form': form}
        if importer_id:
            context['importer'] = Importer.objects.filter(pk=importer_id).get()
        return render(self.request, self.template_name, context)


class ImporterDetailView(ModelDetailView):
    template_name = 'web/importer/view.html'
    model = Importer
    permission_required = \
        'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'

    def get_context_data(self, object):
        context = super().get_context_data()
        context['form'] = ImporterDisplayForm(instance=object)
        return context
