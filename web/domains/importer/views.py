import structlog as logging
from django.urls import reverse_lazy
from django.shortcuts import render, redirect

from web.auth import utils as auth_utils

from web.views import (ModelCreateView, ModelDetailView, ModelFilterView, ModelUpdateView)
from web.views.actions import Archive, Edit, Unarchive, CreateAgent
from web.views.mixins import PostActionMixin

from .forms import ImporterDisplayForm, ImporterEditForm, ImporterFilter
from .models import Importer

from web.domains.office.models import Office
from web.domains.office.forms import OfficeEditForm, OfficeFormSet

from django.forms import formset_factory

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
        fields = [
            'status', ('name', 'user', 'registered_number', 'entity_type'),
            'offices'
        ]
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
            'offices': {
                'header': 'Addresses',
                'show_all': True,
            }
        }
        opts = {'inline': True, 'icon_only': True}
        actions = [
            Archive(**opts),
            Unarchive(**opts),
            CreateAgent(**opts),
            Edit(**opts)
        ]


class ImporterEditView(ModelUpdateView, PostActionMixin):
    template_name = 'web/domains/importer/edit.html'
    success_url = reverse_lazy('importer-list')
    cancel_url = success_url

    def has_permission(self):
        return has_permission(self.request.user)

    def get(self, request, pk, offices_form=None, form=None):
        importer = Importer.objects.get(pk=pk)
        if not form:
            form = ImporterEditForm(instance=importer)

        # should the offices formset be shown on the edit page
        # if we received the form, then we displayed as we want to
        # show the form and errors, otherwise
        show_offices_form = True
        if not offices_form:
            Formset = formset_factory(OfficeEditForm)
            offices_form = Formset()
            show_offices_form = False

        return render(request, self.template_name, {
            'form': form,
            'offices_form': offices_form,
            'success_url': self.success_url,
            'cancel_url': self.cancel_url,
            'view': self,
            'show_offices_form': show_offices_form
        })

    def edit(self, request, pk):
        importer = Importer.objects.get(pk=pk)
        form = ImporterEditForm(request.POST, instance=importer)

        Formset = formset_factory(OfficeEditForm, formset=OfficeFormSet)
        offices_form = Formset(request.POST)

        if not offices_form.is_valid() or not form.is_valid():
            return self.get(request, pk, offices_form=offices_form, form=form)

        importer = form.save()

        for form in offices_form:
            office = form.save()
            importer.offices.add(office)
        importer.save()

        return redirect('importer-view', pk=pk)

    def do_archive(self, request, is_active):
        if 'item' not in request.POST:
            raise NameError()

        office = Office.objects.get(pk=int(request.POST.get('item', 0)))

        if not office:
            raise IndexError()

        office.is_active = is_active
        office.save()

    def archive(self, request, pk):
        self.do_archive(request, False)
        return redirect('importer-edit', pk=pk)

    def unarchive(self, request, pk):
        self.do_archive(request, True)
        return redirect('importer-edit', pk=pk)


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
