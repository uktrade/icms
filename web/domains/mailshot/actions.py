#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.urls import reverse_lazy

from web.views.actions import Edit
from web.views.actions import View as _View

from .models import Mailshot


class Edit(Edit):
    def display(self, mailshot):
        return mailshot.status == Mailshot.DRAFT


class View(_View):
    def display(self, mailshot):
        return mailshot.status != Mailshot.DRAFT


class Retract(Edit):
    icon = 'icon-bin'
    label = 'Retract'

    def href(self, object):
        return reverse_lazy('mailshot-retract', args=(object.id, ))

    def display(self, mailshot):
        return mailshot.status == Mailshot.PUBLISHED
