#!/usr/bin/env python
# -*- coding: utf-8 -*-

import structlog as logging
from django.forms import Form
from django.forms.fields import ChoiceField

from web.forms.mixins import FormFieldConfigMixin

logger = logging.getLogger(__name__)


class ReAssignTaskForm(FormFieldConfigMixin, Form):
    user = ChoiceField(label='Assign To', required=True)

    def __init__(self, users, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug(users)
        self.fields['user'].choices = users

    class Meta:
        fields = []
        labels = {'user': 'Assign To'}
