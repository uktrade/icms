from django.urls import reverse

import web.views.actions as actions

from .models import Mailshot


class Edit(actions.Edit):
    def display(self, mailshot: Mailshot) -> bool:
        return mailshot.status == Mailshot.Statuses.DRAFT


class View(actions.View):
    def display(self, mailshot: Mailshot) -> bool:
        return mailshot.status != Mailshot.Statuses.DRAFT


class ViewReceived(View):
    def href(self, mailshot: Mailshot) -> str:
        return reverse("mailshot-detail-received", kwargs={"mailshot_pk": mailshot.pk})


class Retract(actions.Edit):
    icon = "icon-bin"
    label = "Retract"

    def href(self, mailshot: Mailshot) -> str:
        return reverse("mailshot-retract", kwargs={"mailshot_pk": mailshot.pk})

    def display(self, mailshot: Mailshot) -> bool:
        return mailshot.status == Mailshot.Statuses.PUBLISHED
