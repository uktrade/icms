#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web.forms import ModelEditForm
from django.forms.widgets import Select

from .models import ApprovalRequest


class ApprovalRequestForm(ModelEditForm):
    def __init__(self, team, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['requested_from'].queryset = team.members.all(
        )  # TODO: All members? Check if certain roles or not
        self.fields['requested_from'].empty_label = 'All'

    class Meta:
        model = ApprovalRequest

        fields = ['requested_from']

        labels = {'requested_from': 'Contact'}

        widgets = {'requested_from': Select()}
        config = {
            '__all__': {
                'show_optional_indicator': False,
            }
        }


class ApprovalRequestResponseForm(ModelEditForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['response'].required = True

    class Meta:
        model = ApprovalRequest
        fields = ['response', 'response_reason']
