import structlog as logging
from django.db import transaction
from django.template.response import TemplateResponse

from web.domains.user.models import User
from web.domains.user.views import PeopleSearchView
from web.views.mixins import PostActionMixin

from .models import Role

logger = logging.getLogger(__name__)


class ContactsManagementMixin(PostActionMixin):
    def _remove_from_session(self, name, default=None):
        "Remvove data from session and return"
        value = self.request.session.pop(name, default)
        logger.debug('Removed from session: {name=%s, value=%s} ', name, value)
        return value

    def _get_post_parameter(self, name):
        return self.request.POST.get(name)

    def _get_post_parameter_as_list(self, name):
        return self.request.POST.getlist(name)

    def _add_to_session(self, name, value):
        "Add data to session"
        self.request.session[name] = value
        logger.debug('Saved to session: {name=%s, value=%s} ', name, value)

    def _get_users_by_ids(self, id_list=[]):
        return list(User.objects.filter(pk__in=id_list))

    def _get_role_members(self, roles):
        role_members = {}
        for role in roles:
            members = []
            for user in list(role.user_set.all()):
                members.append(user)
            role_members[str(role.id)] = members

        return role_members

    def _extract_role_members(self):
        role_members = {}
        for key in self.request.POST:
            if ('role_members_') in key:
                members = self.request.POST.getlist(key)
                role_id = key.replace('role_members_', '')
                role_members[role_id] = members
        return role_members

    def _restore_from_session(self, new_members=[], pk=None):
        _pop = self._remove_from_session
        form_data = _pop('form')
        form = self.get_form(data=form_data, pk=pk)
        users = self._get_users_by_ids(_pop('members', []))
        role_members = _pop('role_members', {})
        role_id = _pop('add_to_role')
        if role_id:
            members = role_members.get(str(role_id)) or []
            new_members.extend(members)
            role_members[str(role_id)] = new_members
            logger.debug('Role members: %s', role_members)
        role_members = self._fetch_role_members(role_members)
        new_members = self._get_users_by_ids(new_members)
        for user in users:
            if user not in new_members:
                new_members.append(user)
        return {
            'form': form,
            'contacts': {
                'members': new_members,
                'roles': self._get_roles(form.instance),
                'role_members': role_members
            }
        }

    def _render(self, context={}):
        return TemplateResponse(self.request, self.template_name,
                                context).render()

    def _get(self, request, pk=None):
        "Initial get request"
        self._remove_from_session(request)  # clear session data if exists
        form = self.get_form(pk=pk)
        return self._render({
            'contacts': self._get_initial_data(form.instance),
            'form': form
        })

    def search_people(self, request, pk=None):
        return PeopleSearchView.as_view()(request)

    def add_people(self, request, pk=None):
        # Handles new members added on search users
        selected_users = self._get_post_parameter_as_list('selected_items')
        data = self._restore_from_session(selected_users, pk=pk)
        logger.debug('Members added to object pk: %s', pk)
        return self._render(data)

    def _save_members(self, object):
        members = set(self._get_post_parameter_as_list('members'))
        object.members.clear()
        for member_id in members:
            object.members.add(member_id)

    def _save_role_members(self, object):
        role_members = self._extract_role_members()
        for role in self._get_roles(object):
            members = role_members.get(str(role.id), [])
            role.user_set.clear()
            for user_id in members:
                role.user_set.add(user_id)

    def _clear_session(self):
        team = self.get_object()
        return self._remove_from_session(f'team:{team.id}')

    def _save_to_session(self, request):
        put = self._add_to_session
        team = self.get_object()
        put(f'team:{team.id}', request.POST)

    def get_data(self):
        team = self.get_object()
        roles = team.roles.all()
        members = team.members.all()
        role_members = {}
        for role in roles:
            role_members[role.id] = role.user_set.values_list('id', flat=True)

        return {
            'members': members,
            'roles': roles,
            'role_members': role_members
        }

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(self.get_data())
        return context

    def add_member(self, request, pk=None):
        self._save_to_session(request)
        return PeopleSearchView.as_view()(request)

    def x_get(self, request, pk=None):
        "Initial get request"
        self._remove_from_session(request)  # clear session data if exists

    @transaction.atomic
    def _save(self, request, pk=None):
        logger.debug('Save: %s', pk)
        form = self.get_form(request.POST, pk)
        if not form.is_valid():  # render back to display errors
            return self._render({
                'contacts': self._get_data(form.instance),
                'form': form
            })
        object = form.save()
        self._save_members(object)
        self._save_role_members(object)
        return self.get(request, pk)
