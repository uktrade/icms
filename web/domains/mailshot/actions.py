#!/usr/bin/env python
# -*- coding: utf-8 -*-
from web.views.actions import Edit, View

from .models import Mailshot


class Edit(Edit):
    icon = ''

    def display(self, mailshot):
        return mailshot.status == Mailshot.DRAFT


class View(View):
    icon = ''

    def display(self, mailshot):
        return mailshot.status != Mailshot.DRAFT
