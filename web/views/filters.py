import django_filters as filter
from web import models
from web.base.forms import widgets


class TemplatesFilter(filter.FilterSet):
    # Fields of the model that can be filtered
    template_name = filter.CharFilter(
        lookup_expr='icontains',
        widget=widgets.TextInput,
        help_text='Use % for wildcard searching.')
    application_domain = filter.ChoiceFilter(
        choices=models.Template.DOMAINS, lookup_expr='exact')
    template_type = filter.ChoiceFilter(
        choices=models.Template.TYPES, lookup_expr='exact')

    class Meta:
        model = models.Template
        fields = []  # Django complains without fields set in the meta
