import structlog as logging
from django.urls import reverse_lazy

from web.auth import utils as auth_utils
from web.views import (ModelCreateView, ModelDetailView, ModelFilterView,
                       ModelUpdateView)

from .forms import ImporterDisplayForm, ImporterEditForm, ImporterFilter
from .models import Importer

logger = logging.getLogger(__name__)

permissions = [
    'IMP_MAINTAIN_ALL', 'IMP_EDIT_SECTION5_AUTHORITY',
    'IMP_EDIT_FIREARMS_AUTHORITY'
]


def has_permission(user):
    return auth_utils.has_any_permission(user, permissions)


class ImporterListView(ModelFilterView):
    template_name = 'web/domains/importer/list.html'
    filterset_class = ImporterFilter
    model = Importer
    page_title = 'Maintain Importers'

    def has_permission(self):
        return has_permission(self.request.user)

    class Display:
        fields = [('name', 'user', 'registered_number', 'entity_type')]
        fields_config = {
            'name': {
                'header': 'Importer Name'
            },
            'user': {
                'no_header': True
            },
            'registered_number': {
                'header': 'Importer Reg No'
            },
            'entity_type': {
                'header': 'Importer Entity Type'
            }
        }


class ImporterEditView(ModelUpdateView):
    template_name = 'web/domains/importer/edit.html'
    form_class = ImporterEditForm
    success_url = reverse_lazy('importer-list')
    cancel_url = success_url
    model = Importer

    def has_permission(self):
        return has_permission(self.request.user)


class ImporterCreateView(ModelCreateView):
    template_name = 'web/domains/importer/create.html'
    form_class = ImporterEditForm
    success_url = reverse_lazy('importer-list')
    cancel_url = success_url
    page_title = 'Create Importer'
    model = Importer

    def has_permission(self):
        return has_permission(self.request.user)


class ImporterDetailView(ModelDetailView):
    template_name = 'web/domains/importer/view.html'
    model = Importer

    def has_permission(self):
        return has_permission(self.request.user)

    def get_context_data(self, object):
        context = super().get_context_data()
        context['form'] = ImporterDisplayForm(instance=object)
        return context
