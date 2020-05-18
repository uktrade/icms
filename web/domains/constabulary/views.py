# from web.domains.team.mixins import ContactsManagementMixin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.urls import reverse_lazy

from web.domains.team.models import Role
from web.views import (ModelCreateView, ModelDetailView, ModelFilterView,
                       ModelUpdateView)
from web.views.actions import Archive, Edit, Unarchive

from .forms import ConstabulariesFilter, ConstabularyForm
from .models import Constabulary

permissions = 'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'


class ConstabularyListView(ModelFilterView):
    template_name = 'web/constabulary/list.html'
    model = Constabulary
    filterset_class = ConstabulariesFilter
    permission_required = permissions
    page_title = 'Maintain Constabularies'

    class Display:
        fields = ['name', 'region_verbose', 'email']
        fields_config = {
            'name': {
                'header': 'Constabulary Name',
                'link': True
            },
            'region_verbose': {
                'header': 'Constabulary Region'
            },
            'email': {
                'header': 'Email Address'
            }
        }
        actions = [Archive(), Unarchive(), Edit()]


class ConstabularyCreateView(ModelCreateView):
    template_name = 'web/constabulary/edit.html'
    form_class = ConstabularyForm
    model = Constabulary
    success_url = reverse_lazy('constabulary-list')
    cancel_url = success_url
    permission_required = permissions
    page_title = 'New Constabulary'

    @transaction.atomic
    def form_valid(self, form):
        """
            Create new constabulary role for firearms authority management for importers
        """
        response = super().form_valid(form)
        role_name = f'Constabulary Contacts:Verified Firearms Authority Editor:{self.object.id}'
        role_description = 'Users in this role have privileges to view and edit \
            importer verified firearms authorities issued by the constabulary.'

        permission_code = f'IMP_CONSTABULARY_CONTACTS:FIREARMS_AUTHORITY_EDITOR:{self.object.id}:IMP_EDIT_FIREARMS_AUTHORITY'  # noqa: C0301

        role = Role.objects.create(name=role_name,
                                   description=role_description,
                                   role_order=10)
        permission = Permission.objects.create(
            codename=permission_code,
            name='Verified Firearms Authority Editor',
            content_type=ContentType.objects.get_for_model(Constabulary))
        role.permissions.add(permission)
        return response


class ConstabularyEditView(ModelUpdateView):
    template_name = 'web/constabulary/edit.html'
    form_class = ConstabularyForm
    model = Constabulary
    success_url = reverse_lazy('constabulary-list')
    cancel_url = success_url
    permission_required = permissions


class ConstabularyDetailView(ModelDetailView):
    form_class = ConstabularyForm
    model = Constabulary
    success_url = reverse_lazy('constabulary-list')
    cancel_url = success_url
    permission_required = permissions
