from django.urls import reverse_lazy
from web.views import (ModelCreateView, ModelDetailView, ModelFilterView,
                       ModelUpdateView)

from .forms import ExporterEditForm, ExporterFilter, ExporterDisplayForm
from .models import Exporter


class ExporterListView(ModelFilterView):
    template_name = 'web/exporter/list.html'
    filterset_class = ExporterFilter
    model = Exporter
    permission_required = \
        'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'

    class Display:
        fields = ['name']
        headers = ['Exporter Name']
        edit = True
        view = True
        archive = True


class ExporterEditView(ModelUpdateView):
    template_name = 'web/exporter/edit.html'
    form_class = ExporterEditForm
    success_url = reverse_lazy('exporter-list')
    model = Exporter
    permission_required = \
        'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'


class ExporterCreateView(ModelCreateView):
    template_name = 'web/exporter/create.html'
    form_class = ExporterEditForm
    success_url = reverse_lazy('exporter-list')
    model = Exporter
    permission_required = \
        'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'


class ExporterDetailView(ModelDetailView):
    template_name = 'web/exporter/view.html'
    model = Exporter
    permission_required = \
        'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'

    def get_context_data(self, object):
        context = super().get_context_data()
        context['form'] = ExporterDisplayForm(instance=object)
        return context
