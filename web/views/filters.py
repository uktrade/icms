import django_filters as filter
from web import models
from web.base.forms import widgets


class TemplatesFilter(filter.FilterSet):
    # Fields of the model that can be filtered
    template_name = filter.CharFilter(
        lookup_expr='icontains',
        widget=widgets.TextInput,
        help_text='Use % for wildcard searching.',
        label='Template Name')
    application_domain = filter.ChoiceFilter(
        choices=models.Template.DOMAINS,
        lookup_expr='exact',
        label='Adpplication Domain')
    template_type = filter.ChoiceFilter(
        choices=models.Template.TYPES,
        lookup_expr='exact',
        label='Template Type')

    class Meta:
        model = models.Template
        fields = []  # Django complains without fields set in the meta


class OutboundEmailsFilter(filter.FilterSet):
    # Fields of the model that can be filtered
    to_name = filter.CharFilter(
        lookup_expr='icontains', widget=widgets.TextInput, label='To Name')
    to_email = filter.CharFilter(
        lookup_expr='icontains', widget=widgets.TextInput, label='To Address')
    subject = filter.CharFilter(
        lookup_expr='icontains', widget=widgets.TextInput, label='Subject')
    sent_from = filter.DateFilter(
        field_name='last_requested_date', lookup_expr='gte', label='Sent From')
    to = filter.DateFilter(
        field_name='last_requested_date', lookup_expr='lte', label='To')
    status = filter.ChoiceFilter(
        choices=models.OutboundEmail.STATUSES, lookup_expr='icontains')

    class Meta:
        model = models.OutboundEmail
        fields = []
