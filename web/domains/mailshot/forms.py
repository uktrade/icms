#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django_filters import CharFilter, ChoiceFilter
from web.forms import ModelSearchFilter

from .models import Mailshot


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
