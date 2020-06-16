import structlog as logging
from django.urls import reverse_lazy

from web.auth import utils as auth_utils
from web.views import (ModelCreateView, ModelDetailView, ModelFilterView,
                       ModelUpdateView)

from .forms import ImporterDisplayForm, ImporterEditForm, ImporterFilter
from .models import Importer
from web.views.actions import Archive, Edit, Unarchive, CreateAgent

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
        fields = ['status', ('name', 'user', 'registered_number', 'entity_type'), 'offices']
        fields_config = {
            'name': {
                'header': 'Importer Name',
                'link': True,
            },
            'user': {
                'no_header': True,
            },
            'registered_number': {
                'header': 'Importer Reg No',
            },
            'entity_type': {
                'header': 'Importer Entity Type',
            },
            'status': {
                'header': 'Status',
                'bold': True,
            },
            'offices' : {
                'header': 'Addresses',
                'show_all': True,
            }
        }
        opts = {'inline': True, 'icon_only': True}
        actions = [Archive(**opts), Unarchive(**opts), CreateAgent(**opts), Edit(**opts)]


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
    form_class = ImporterDisplayForm
    model = Importer

    def has_permission(self):
        return has_permission(self.request.user)

    def get_context_data(self, object):
        context = super().get_context_data(object)
        context['form'] = ImporterDisplayForm(instance=object)
        return context
