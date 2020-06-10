import structlog as logging
from django.db import transaction
from django.template.response import TemplateResponse

from web.domains.user.models import User
from web.domains.user.views import PeopleSearchView
from web.utils.session import Session
from web.views.mixins import PostActionMixin

logger = logging.getLogger(__name__)


class ContactsManagementMixin(PostActionMixin):
    def _search_people(self):
        return PeopleSearchView.as_view()(self.request)

    def _session(self):
        return Session(self.request)

    def _get_users_by_ids(self, id_list=[]):
        return list(User.objects.filter(pk__in=id_list))

    def _extract_role_members(self, data):
        role_members = {}
        for key in data:
            if 'role_members_' in key:
                members = self.request.POST.getlist(key)
                role_id = key.replace('role_members_', '')
                role_members[role_id] = members
        return role_members

    def _get_form(self, data=None):
        form_class = self.get_form_class()
        team = self.get_object()
        return form_class(instance=team, data=data)

    def _load_data(self):
        """
            Load initial data from database
        """
        team = self.get_object()
        roles = team.roles.all()
        members = team.members.all()
        role_members = {}
        for role in roles:
            # Create role_id -> member_ids mapping with ids as strings
            role_members[str(role.id)] = list(
                map(str, role.user_set.values_list('id', flat=True)))

        return {
            'form': self._get_form(),
            'members': members,
            'roles': roles,
            'role_members': role_members
        }

    def _remove_from_session(self):
        team = self.get_object()
        return self._session().pop(f'team:{team.id}')

    def _restore_from_session(self, new_members=None):
        """
            Load data saved to session previously
        """
        team = self.get_object()
        data = self._remove_from_session()
        members = data.get('members')
        members.extend(new_members)
        members = self._get_users_by_ids(members)

        return {
            'form': self._get_form(data.get('form')),
            'members': members,
            'roles': team.roles.all(),
            'role_members': data.get('role_members')
        }

    def _get_posted_context(self, form):
        team = self.get_object()
        data = self.request.POST
        members = data.getlist('members')
        members = self._get_users_by_ids(members)
        response = {
            'form': form,
            'members': members,
            'roles': team.roles.all(),
            'role_members': self._extract_role_members(data)
        }
        return response

    def _save_to_session(self):
        team = self.get_object()
        data = self.request.POST
        self._session().put(
            f'team:{team.id}', {
                'form': self._get_form(data=data).data,
                'members': data.getlist('members'),
                'role_members': self._extract_role_members(data)
            })

    def _render(self, request, context):
        self.object = self.get_object()
        data = super().get_context_data()
        data.update(context)
        return TemplateResponse(request, self.template_name, data)

    def search_people(self, request, *args, **kwargs):
        return self._search_people()

    def add_people(self, request, *args, **kwargs):
        """Handles new members added in search people page"""
        new_members = request.POST.getlist('selected_items')
        context = self._restore_from_session(new_members)
        return self._render(request, context)

    def add_member(self, request, *args, **kwargs):
        """ Render search people page if add_member action is received """
        self._save_to_session()
        return self._search_people()

    def get(self, request, *args, **kwargs):
        "Initial get request"
        self._remove_from_session()  # clear session data if exists
        return self._render(request, self._load_data())

    def _save_members(self, team):
        members = set(self.request.POST.getlist('members'))
        team.members.clear()
        for member_id in members:
            team.members.add(member_id)

    def _save_role_members(self, team):
        role_members = self._extract_role_members(self.request.POST)
        for role in team.roles.all():
            members = role_members.get(str(role.id), [])
            role.user_set.clear()
            for user_id in members:
                role.user_set.add(user_id)

    @transaction.atomic
    def save(self, request, *args, **kwargs):
        form = self._get_form(request.POST)
        if not form.is_valid():  # render back to display errors
            return self._render(request, self._get_posted_context(form))

        team = form.save()
        self._save_members(team)
        self._save_role_members(team)
        return self.get(request, *args, **kwargs)
