#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web.views import ModelFilterView

from .actions import Edit, View
from .models import Mailshot
from .forms import MailshotFilter


class MailshotListView(ModelFilterView):
    template_name = 'web/mailshot/list.html'
    model = Mailshot
    filterset_class = MailshotFilter
    permission_required = []
    page_title = 'Maintain Mailshots'

    class Display:
        fields = [
            'id', 'status_verbose', ('retracted', 'published', 'started'),
            'title', 'description'
        ]
        fields_config = {
            'id': {
                'header': 'Reference'
            },
            'started': {
                'header': 'Activity',
                'label': '<strong>Started</strong>'
            },
            'published': {
                'no_header': True,
                'label': '<strong>Published</strong>'
            },
            'retracted': {
                'no_header': True,
                'label': '<strong>Retracted</strong>'
            },
            'title': {
                'header': 'Title'
            },
            'status_verbose': {
                'header': 'Status'
            },
            'description': {
                'header': 'Description'
            }
        }
        actions = [Edit(), View()]
