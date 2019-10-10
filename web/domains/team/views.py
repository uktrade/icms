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
    page_title = 'Search Teams'

    def get_queryset(self):
        """ Only list teams the user is part of"""
        """ Super users has access to all"""
        if self.request.user.is_superuser:
            return super().get_queryset()

        return self.request.user.team_set.all()

    def has_permission(self):
        """ Allow viewing of teams if user is part of group"""
        if self.request.user.is_superuser:
            return True

        return self.request.user.groups.count() > 0

    class Display:
        fields = ['name']
        headers = ['Name']
        edit = True


class TeamEditView(ContactsManagementMixin, ModelUpdateView):
    template_name = 'web/team/edit.html'
    form_class = TeamEditForm
    success_url = reverse_lazy('team-list')
    model = Team

    def get_page_title(self):
        return f"Editing '{self.object.name}'"

    def has_permission(self):
        """ Allows going on to edit screen if user is part of the team """

        if self.request.user.is_superuser:
            return True

        team = self.get_object()
        teams = self.request.user.team_set.all()
        if team in teams:
            return True

        return False
