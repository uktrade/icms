from django.urls import reverse

import web.views.actions as actions

from .models import Mailshot


class Edit(actions.Edit):
    def display(self, mailshot):
        return mailshot.status == Mailshot.Statuses.DRAFT


class View(actions.View):
    def display(self, mailshot):
        return mailshot.status != Mailshot.Statuses.DRAFT


class ViewReceived(View):
    def href(self, object):
        return reverse("mailshot-detail-received", kwargs={"mailshot_pk": object.pk})


class Retract(actions.Edit):
    icon = "icon-bin"
    label = "Retract"

    def href(self, object):
        return reverse("mailshot-retract", kwargs={"mailshot_pk": object.pk})

    def display(self, mailshot):
        return mailshot.status == Mailshot.Statuses.PUBLISHED
