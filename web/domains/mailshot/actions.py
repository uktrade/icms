#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.urls import reverse_lazy

import web.views.actions as actions

from .models import Mailshot


class Edit(actions.Edit):
    def display(self, mailshot):
        return mailshot.status == Mailshot.DRAFT


class View(actions.View):
    def display(self, mailshot):
        return mailshot.status != Mailshot.DRAFT


class Retract(actions.Edit):
    icon = "icon-bin"
    label = "Retract"

    def href(self, object):
        return reverse_lazy("mailshot-retract", args=(object.id,))

    def display(self, mailshot):
        return mailshot.status == Mailshot.PUBLISHED
