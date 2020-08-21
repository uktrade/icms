#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.forms import ModelForm

from .models import ApprovalRequest


class ApprovalRequestResponseForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["response"].required = True

    class Meta:
        model = ApprovalRequest
        fields = ["response", "response_reason"]
