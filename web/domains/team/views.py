from django.urls import reverse_lazy
# from django_filters import CharFilter
from web.views import ModelFilterView, ModelUpdateView

from .forms import TeamEditForm, TeamsFilter
from .mixins import ContactsManagementMixin
from .models import Team


class TeamListView(ModelFilterView):
    template_name = 'web/team/list.html'
    filterset_class = TeamsFilter
    model = Team
    config = {'title': 'Search Teams'}

    class Display:
        fields = ['name']
        headers = ['Name']
        edit = True


class TeamEditView(ContactsManagementMixin, ModelUpdateView):
    template_name = 'web/team/edit.html'
    form_class = TeamEditForm
    success_url = reverse_lazy('team-list')
    model = Team
    config = {'title': 'Edit Teams'}
