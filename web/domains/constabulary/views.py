from web.domains.team.mixins import ContactsManagementMixin
from web.views import ModelCreateView, ModelFilterView, ModelUpdateView

from .forms import ConstabulariesFilter, ConstabularyForm
from .models import Constabulary


class ConstabularyListView(ModelFilterView):
    template_name = 'web/constabulary/list.html'
    model = Constabulary
    filterset_class = ConstabulariesFilter

    class Display:
        fields = ['name', 'region_verbose', 'email']
        headers = ['Constabulary Name', 'Constabulary Region', 'Email Address']
        edit = True
        archive = True


class ConstabularyCreateView(ContactsManagementMixin, ModelCreateView):
    template_name = 'web/constabulary/edit.html'
    form_class = ConstabularyForm
    model = Constabulary
    config = {'title': 'New Constabulary'}


class ConstabularyEditView(ContactsManagementMixin, ModelUpdateView):
    template_name = 'web/constabulary/edit.html'
    form_class = ConstabularyForm
    model = Constabulary
    config = {'title': 'Edit Constabulary'}
