#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect
from viewflow.flow.views.start import BaseStartFlowMixin
from viewflow.flow.views.task import BaseFlowMixin


class SimpleStartFlowMixin(BaseStartFlowMixin):
    """StartFlowMixin without MessageUserMixin"""
    def activation_done(self):
        """Finish task activation."""
        self.activation.done()

    def form_valid(self, *args, **kwargs):
        """
        If the form is valid, save the associated model and finish the task.
        """
        super().form_valid(*args, **kwargs)
        self.activation_done()
        return HttpResponseRedirect(self.get_success_url())


class SimpleFlowMixin(BaseFlowMixin):
    """FlowMixin without MessageUserMixin."""
    def activation_done(self):
        """Finish the task activation."""
        self.activation.done()

    def form_valid(self, form, **kwargs):
        """If the form is valid, save the associated model and finish the task."""
        super().form_valid(form, **kwargs)
        form.save()
        self.activation_done()
        return HttpResponseRedirect(self.get_success_url())
