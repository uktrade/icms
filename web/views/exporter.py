import logging

from django.urls import reverse_lazy
from django_filters import BooleanFilter, CharFilter, ChoiceFilter, DateFilter
from web.base.forms import FilterSet, ModelForm, ReadOnlyFormMixin, widgets
from web.base.forms.fields import CharField, ChoiceField, DisplayField
from web.base.views import (SecureCreateView, SecureDetailView,
                            SecureFilteredListView, SecureUpdateView)
from web.models import Exporter

from .filters import _filter_config

logger = logging.getLogger(__name__)


class ExporterFilter(FilterSet):
    exporter_name = CharFilter(field_name='name',
                               lookup_expr='icontains',
                               widget=widgets.TextInput,
                               label='Exporter Name')

    class Meta:
        config = _filter_config


class ExporterEditForm(ModelForm):
    class Meta:
        model = Exporter
        fields = ['name', 'registered_number', 'comments']
        labels = {'name': 'Organisation Name'}
        config = _filter_config


class ExporterDisplayForm(ReadOnlyFormMixin, ExporterEditForm):
    pass


class ExporterCreateForm(ExporterEditForm):
    class Meta(ExporterEditForm.Meta):
        pass


class ExporterListView(SecureFilteredListView):
    template_name = 'web/exporter/list.html'
    filterset_class = ExporterFilter
    model = Exporter
    paginate_by = 100


class ExporterEditView(SecureUpdateView):
    template_name = 'web/exporter/edit.html'
    form_class = ExporterEditForm
    success_url = reverse_lazy('exporter-list')
    model = Exporter


class ExporterCreateView(SecureCreateView):
    template_name = 'web/exporter/create.html'
    form_class = ExporterCreateForm
    success_url = reverse_lazy('exporter-list')
    model = Exporter


class ExporterDetailView(SecureDetailView):
    template_name = 'web/exporter/view.html'
    model = Exporter

    def get_context_data(self, object):
        context = super().get_context_data()
        context['form'] = ExporterDisplayForm(instance=object)
        return context

    class Meta:
        config = _filter_config
