#!/usr/bin/env python
# -*- coding: utf-8 -*-

import structlog as logging
from django.forms import Form, ModelChoiceField

from web.forms.mixins import FormFieldConfigMixin

logger = logging.getLogger(__name__)


class ReAssignTaskForm(FormFieldConfigMixin, Form):
    user = ModelChoiceField(queryset=None, label='Assign To', required=True)

    def __init__(self, users_queryset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = users_queryset

    class Meta:
        fields = []
        labels = {'user': 'Assign To'}
