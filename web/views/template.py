from django_filters import (CharFilter, ChoiceFilter)
from web.base.views import ModelListActionView
from web.base.forms import FilterSet, widgets
from web.models import Template
from .filters import _filter_config


class TemplatesFilter(FilterSet):
    # Fields of the model that can be filtered
    template_name = CharFilter(
        lookup_expr='icontains',
        widget=widgets.TextInput,
        help_text='Use % for wildcard searching.',
        label='Template Name')
    application_domain = ChoiceFilter(
        choices=Template.DOMAINS,
        lookup_expr='exact',
        label='Adpplication Domain')
    template_type = ChoiceFilter(
        choices=Template.TYPES, lookup_expr='exact', label='Template Type')

    class Meta:
        model = Template
        fields = []  # Django complains without fields set in the meta
        config = _filter_config


class TemplateListView(ModelListActionView):
    template_name = 'web/template/list.html'
    model = Template
    filter_class = TemplatesFilter
