#!/usr/bin/env python
# -*- coding: utf-8 -*-
from web.views.actions import Edit, View

from .models import Mailshot


class Edit(Edit):
    def display(self, mailshot):
        return mailshot.status == Mailshot.DRAFT


class View(View):
    icon = 'icon-eye'

    def display(self, mailshot):
        return mailshot.status != Mailshot.DRAFT


class Retract(Edit):
    icon = 'icon-bin'
    label = 'Retract'

    def href(self, object):
        return f'{object.id}/retract/'

    def display(self, mailshot):
        return mailshot.status == Mailshot.PUBLISHED
