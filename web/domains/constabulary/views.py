from web.domains.team.mixins import ContactsManagementMixin
from web.views import ModelCreateView, ModelFilterView, ModelUpdateView

from .forms import ConstabulariesFilter, ConstabularyForm
from .models import Constabulary


class ConstabularyListView(ModelFilterView):
    template_name = 'web/constabulary/list.html'
    model = Constabulary
    filterset_class = ConstabulariesFilter
    config = {'title': 'Maintain Constabularies'}


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
