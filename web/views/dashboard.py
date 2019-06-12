from django.shortcuts import render
from django_filters import (CharFilter, ChoiceFilter, DateFilter)
from web.auth.decorators import require_registered
from web.base.forms import FilterSet, widgets
from web.models import OutboundEmail
from .filters import _filter_config


@require_registered
def outbound_emails(request):
    filter = OutboundEmailsFilter(
        request.GET,
        queryset=OutboundEmail.objects.all().prefetch_related('attachments'))
    return render(request, 'web/portal/outbound-emails.html',
                  {'filter': filter})


class OutboundEmailsFilter(FilterSet):
    # Fields of the model that can be filtered
    to_name = CharFilter(
        lookup_expr='icontains', widget=widgets.TextInput, label='To Name')
    to_email = CharFilter(
        lookup_expr='icontains', widget=widgets.TextInput, label='To Address')
    subject = CharFilter(
        lookup_expr='icontains', widget=widgets.TextInput, label='Subject')
    sent_from = DateFilter(
        field_name='last_requested_date',
        widget=widgets.DateInput,
        lookup_expr='gte',
        label='Sent From')
    to = DateFilter(
        field_name='last_requested_date',
        widget=widgets.DateInput,
        lookup_expr='lte',
        label='To')
    status = ChoiceFilter(
        choices=OutboundEmail.STATUSES,
        lookup_expr='icontains',
        label='Status')

    class Meta:
        model = OutboundEmail
        fields = []
        config = _filter_config
