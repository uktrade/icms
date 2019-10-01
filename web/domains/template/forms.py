from django_filters import CharFilter, ChoiceFilter
from web.forms import ModelSearchFilter

from .models import Template


class TemplatesFilter(ModelSearchFilter):
    # Fields of the model that can be filtered
    template_name = CharFilter(lookup_expr='icontains',
                               help_text='Use % for wildcard searching.',
                               label='Template Name')
    application_domain = ChoiceFilter(choices=Template.DOMAINS,
                                      lookup_expr='exact',
                                      label='Adpplication Domain')
    template_type = ChoiceFilter(choices=Template.TYPES,
                                 lookup_expr='exact',
                                 label='Template Type')

    class Meta:
        model = Template
        fields = []  # Django complains without fields set in the meta
