#!/usr/bin/env python
# -*- coding: utf-8 -*-

import structlog as logging
from django.forms import CharField, MultipleChoiceField
from django.forms.widgets import CheckboxSelectMultiple, Textarea

from django_filters import CharFilter, ChoiceFilter
from web.forms import ModelEditForm, ModelSearchFilter

from .models import Mailshot

logger = logging.get_logger(__name__)


class MailshotFilter(ModelSearchFilter):

    id = CharFilter(field_name='id',
                    lookup_expr='icontains',
                    label='Reference')

    title = CharFilter(field_name='title',
                       lookup_expr='icontains',
                       label='Title')

    description = CharFilter(field_name='description',
                             lookup_expr='icontains',
                             label='Description')

    status = ChoiceFilter(field_name='status',
                          lookup_expr='exact',
                          choices=Mailshot.STATUSES,
                          label='Status')

    class Meta:
        model = Mailshot
        fields = []


class MailshotForm(ModelEditForm):

    RECIPIENT_CHOICES = (('importers', 'Importers and Agents'),
                         ('exporters', 'Exporters and Agents'))

    reference = CharField(disabled=True, required=False)
    status = CharField(disabled=True, required=False)
    recipients = MultipleChoiceField(choices=RECIPIENT_CHOICES,
                                     widget=CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reference'].initial = self.instance.id
        self.fields['status'].initial = self.instance.status_verbose
        recipients = []
        if self.instance.is_to_importers:
            recipients.append('importers')
        if self.instance.is_to_exporters:
            recipients.append('exporters')
        self.fields['recipients'].initial = recipients

    def clean_recipients(self):
        recipients = self.cleaned_data['recipients']
        self.instance.is_to_importers = 'importers' in recipients
        self.instance.is_to_exporters = 'exporters' in recipients
        return self.cleaned_data['recipients']

    class Meta:
        model = Mailshot
        fields = [
            'reference', 'status', 'title', 'description', 'is_email',
            'email_subject', 'email_body', 'recipients'
        ]
        widgets = {
            'description': Textarea({
                'rows': 4,
                'cols': 50
            }),
            'email_body': Textarea({
                'rows': 4,
                'cols': 50
            })
        }
        labels = {
            'is_email': 'Send Emails',
            'email_subject': 'Email Subject',
            'email_body': 'Email Body',
        }
        help_texts = {
            'title':
            "The mailshot title will appear in the recipient's workbasket.",
            'is_email':
            "Optionally send emails to the selected recipients. Note that uploaded documents will not be attached to the email."
        }
        config = {'__all__': {'show_optional_indicator': False}}
