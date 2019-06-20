from django.db import transaction
from django.shortcuts import (render, redirect)
from web.base.views import PostActionMixin
from web.models import User, Role
from .user import search_people


class ContactsManagementMixin(PostActionMixin):
    def _remove_from_session(self, name, default=None):
        "Remvove data from session and return"
        return self.request.session.pop(name, default)

    def _get_post_parameter(self, name):
        return self.request.POST.get(name)

    def _get_post_parameter_as_list(self, name):
        return self.request.POST.getlist(name)

    def _add_to_session(self, name, value):
        "Add data to session"
        self.request.session[name] = value

    def _get_role_members(self, roles):
        role_members = {}
        for role in roles:
            members = []
            for user in list(role.user_set.all().only('id')):
                members.append(str(user.id))
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

    def _get_users_by_ids(self, id_list=[]):
        return list(User.objects.filter(pk__in=id_list))

    def _get_roles(self, object):
        if not object.id:  # New object
            return Role.objects.none()

        return object.roles.all()

    def _get_data(self, object):
        param = self._get_post_parameter_as_list
        roles = self._get_roles(object)
        members = self._get_users_by_ids(param('members'))
        return {
            'members': members,
            'addresses': param('addresses'),
            'roles': roles,
            'role_members': self._extract_role_members()
        }

    def _get_initial_data(self, object):
        if not object.id:  # New Object
            return {}

        roles = object.roles.all()
        # TODO: might be slow, use Django api to fetch related efficientl
        return {
            'members': object.members.all(),
            'addresses': object.addresses.all(),
            'roles': roles,
            'role_members': self._get_role_members(roles)
        }

    def _save_to_session(self):
        put = self._add_to_session
        param = self._get_post_parameter_as_list
        form_data = self.get_form(self.request.POST).data
        put('form', form_data)
        put('members', param('members'))
        put('addresses', param('addresses'))
        put('role_members', self._extract_role_members())

    def _restore_from_session(self, request, new_members=[]):
        _pop = self._remove_from_session
        form_data = _pop('form')
        form = self.get_form(data=form_data)
        users = self._get_users_by_ids(_pop('members', []))
        for user in users:
            if user not in new_members:
                new_members.append(user)
        return {
            'form': form,
            'contacts': {
                'members': new_members,
                'addresses': _pop('addresses'),
                'roles': self._get_roles(form.instance),
                'role_members': _pop('role_members')
            }
        }

    def _render(self, context={}):
        return render(self.request, self.template_name, context)

    def get_form(self, data=None, pk=None):
        instance = None
        if pk:
            instance = super().get_object()

        return super().get_form_class()(data, instance=instance)

    def get(self, request, pk=None):
        "Initial get request"
        self._remove_from_session(request)  # clear session data if exists
        form = self.get_form(pk=pk)
        return self._render({
            'contacts': self._get_initial_data(form.instance),
            'form': form
        })

    def add_member(self, request, pk=None):
        self._save_to_session()
        return search_people(request)

    def add_people(self, request, pk=None):
        # Handles new members added on search users
        selected_users = self._get_post_parameter_as_list('selected_items')
        new_members = self._get_users_by_ids(selected_users)
        data = self._restore_from_session(request, new_members)
        return self._render(data)

    def _save_members(self, object):
        members = self._get_post_parameter_as_list('members')
        object.members.clear()
        for member_id in members:
            object.members.add(member_id)

    def _save_role_members(self, object):
        role_members = self._extract_role_members()
        for role in self._get_roles(object):
            members = role_members.get(str(role.id), [])
            role.user_set.clear()
            for member_id in members:
                role.user_set.add(member_id)

    @transaction.atomic
    def save(self, request, pk=None):
        form = self.get_form(request.POST)
        if not form.is_valid():  # render back to display errors
            return self._render({
                'contacts': self._get_data(form.instance),
                'form': form
            })
        object = form.save()
        self._save_members(object)
        self._save_role_members(object)
        return self.get(request, pk)
