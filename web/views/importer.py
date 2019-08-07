import logging

from django.db.models.functions import Concat
from django.shortcuts import render
from django.urls import reverse_lazy
from django_filters import BooleanFilter, CharFilter, ChoiceFilter, DateFilter
from web.base.forms import FilterSet, ModelForm, ReadOnlyFormMixin, widgets
from web.base.forms.fields import CharField, ChoiceField, DisplayField
from web.base.views import (SecureCreateView, SecureDetailView,
                            SecureFilteredListView, SecureUpdateView)
from web.models import Importer

from .contacts import ContactsManagementMixin
from .filters import _filter_config

logger = logging.getLogger(__name__)


class ImporterFilter(FilterSet):
    importer_entity_type = CharFilter(field_name='type',
                                      lookup_expr='icontains',
                                      widget=widgets.TextInput,
                                      label='Importer Entity Type')

    importer_name = CharFilter(lookup_expr='icontains',
                               widget=widgets.TextInput,
                               label='Importer Name',
                               method='filter_importer_name')

    # Filter base queryset to only get importers that are not agents.
    @property
    def qs(self):
        queryset = super().qs
        return queryset.filter(main_importer__isnull=True)

    def filter_importer_name(self, queryset, name, value):
        if not value:
            return queryset

        #  Filter concatanation of title name and last name in case the importer
        #  to cover both individual importers and organisations
        # see manager.py for annotated queryset to filter in concatanated
        return queryset.filter(full_name__icontains=value)

    #  valid_end = DateFilter(field_name='validity_end_date',
    #  widget=widgets.DateInput,
    #  lookup_expr='lte',
    #  label='and')

    #  is_archived = BooleanFilter(field_name='is_active',
    #  widget=widgets.CheckboxInput,
    #  lookup_expr='exact',
    #  exclude=True,
    #  label='Search Archived')
    #

    class Meta:
        model = Importer
        fields = []
        config = _filter_config


class ImporterEditForm(ModelForm):
    type = ChoiceField(choices=Importer.TYPES)

    class Meta:
        model = Importer
        fields = [
            'type', 'title', 'name', 'last_name', 'email', 'phone',
            'region_origin', 'comments'
        ]
        labels = {'type': 'Entity Type', 'first_name': 'Forename'}
        config = _filter_config


class ImporterDisplayForm(ReadOnlyFormMixin, ImporterEditForm):
    pass


class ImporterCreateForm(ImporterEditForm):
    class Meta(ImporterEditForm.Meta):
        pass


class ImporterListView(SecureFilteredListView):
    template_name = 'web/importer/list.html'
    filterset_class = ImporterFilter
    model = Importer
    paginate_by = 100


class ImporterEditView(ContactsManagementMixin, SecureUpdateView):
    template_name = 'web/importer/edit.html'
    form_class = ImporterEditForm
    success_url = reverse_lazy('importer-list')
    model = Importer

    def get(self, request, pk, importer_id=None):
        form = super().get_form(pk=pk)
        context = {
            'contacts': self._get_initial_data(form.instance),
            'form': form
        }
        if importer_id:
            context['importer'] = Importer.objects.filter(pk=importer_id).get()
        return self._render(context)


class ImporterCreateView(SecureCreateView):
    template_name = 'web/importer/create.html'
    form_class = ImporterCreateForm
    success_url = reverse_lazy('importer-list')
    model = Importer

    def get(self, request, importer_id=None):
        form = super().get_form()
        context = {'form': form}
        if importer_id:
            context['importer'] = Importer.objects.filter(pk=importer_id).get()
        return render(self.request, self.template_name, context)


class ImporterDetailView(SecureDetailView):
    template_name = 'web/importer/view.html'
    model = Importer

    def get_context_data(self, object):
        context = super().get_context_data()
        context['form'] = ImporterDisplayForm(instance=object)
        return context

    class Meta:
        config = _filter_config
