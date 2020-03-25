from django_filters import CharFilter
from web.forms import ModelDisplayForm, ModelEditForm, ModelSearchFilter

from .models import Exporter


class ExporterFilter(ModelSearchFilter):
    exporter_name = CharFilter(field_name='name',
                               lookup_expr='icontains',
                               label='Exporter Name')

    agent_name = CharFilter(field_name='agents__name',
                            lookup_expr='icontains',
                            label='Agent Name')

    class Meta:
        model = Exporter
        fields = []


class ExporterEditForm(ModelEditForm):
    class Meta:
        model = Exporter
        fields = ['name', 'registered_number', 'comments']
        labels = {'name': 'Organisation Name'}


class ExporterDisplayForm(ModelDisplayForm):
    pass
