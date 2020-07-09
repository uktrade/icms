from django.db.models import Q
from django.urls import reverse_lazy

# from django_filters import CharFilter
from web.views import ModelFilterView, ModelUpdateView
from web.views.actions import Edit

from .forms import TeamEditForm, TeamsFilter
from .mixins import ContactsManagementMixin
from .models import Role, Team


class TeamListView(ModelFilterView):
    template_name = "web/domains/team/list.html"
    filterset_class = TeamsFilter
    model = Team
    page_title = "Search Teams"
    paginate = False

    def get_queryset(self):
        """
            Only list the teams user is part of as 'Resource Co-ordinator'
            or 'Team Coordinator(s)'.
            Super users has access to all
        """
        user = self.request.user
        teams_query = super().get_queryset()
        if user.is_superuser:
            return teams_query

        return teams_query.filter(
            roles__in=Role.objects.filter(
                group__in=user.groups.filter(
                    Q(name__contains=":Team Coordinator")
                    | Q(name__contains=":Resource Co-ordinator")
                ).all()
            )
        )

    def has_permission(self):
        """
            Allow viewing of teams if user is part of any team as 'Resource Co-ordinator'
            or 'Team Coordinator(s)'
        """
        if self.request.user.is_superuser:
            return True

        return self.get_queryset().exists()

    class Display:
        fields = ["name"]
        fields_config = {"name": {"header": "Name"}}
        actions = [Edit()]


class TeamEditView(ContactsManagementMixin, ModelUpdateView):
    template_name = "web/domains/team/edit.html"
    form_class = TeamEditForm
    success_url = reverse_lazy("team-list")
    cancel_url = success_url
    model = Team

    def get_page_title(self):
        return f"Editing '{self.object.name}'"

    def has_permission(self):
        """
            Allow access if user is a part of the team as Resource Co-ordinator
            or Team Coordinator(s)
        """
        if self.request.user.is_superuser:
            return True

        team = self.get_object()
        coordinator_role = team.roles.get(
            Q(name__contains=":Team Coordinator") | Q(name__contains=":Resource Co-ordinator")
        )
        return coordinator_role.user_set.filter(pk=self.request.user.pk).exists()
