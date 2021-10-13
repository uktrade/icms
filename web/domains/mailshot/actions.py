from typing import Any

from django.urls import reverse

import web.views.actions as actions

from .models import Mailshot


class Edit(actions.Edit):
    def display(self, mailshot: Mailshot) -> bool:
        return mailshot.status == Mailshot.Statuses.DRAFT

    def get_context_data(self, mailshot: Mailshot) -> dict[str, Any]:
        context = super().get_context_data(mailshot)
        context["icon"] = None

        return context


class View(actions.View):
    def display(self, mailshot: Mailshot) -> bool:
        return mailshot.status != Mailshot.Statuses.DRAFT

    def get_context_data(self, mailshot: Mailshot) -> dict[str, Any]:
        context = super().get_context_data(mailshot)
        context["icon"] = None

        return context


class ViewReceived(View):
    def href(self, mailshot: Mailshot) -> str:
        return reverse("mailshot-detail-received", kwargs={"mailshot_pk": mailshot.pk})


class Retract(actions.Edit):
    label = "Retract"

    def href(self, mailshot: Mailshot) -> str:
        return reverse("mailshot-retract", kwargs={"mailshot_pk": mailshot.pk})

    def display(self, mailshot: Mailshot) -> bool:
        return mailshot.status == Mailshot.Statuses.PUBLISHED

    def get_context_data(self, mailshot: Mailshot) -> dict[str, Any]:
        context = super().get_context_data(mailshot)
        context["icon"] = None

        return context


class Republish(actions.PostAction):
    label = "Republish"
    confirm = False
    inline = True
    template = "model/actions/post-inline.html"

    def display(self, mailshot: Mailshot) -> bool:
        retracted = mailshot.status == Mailshot.Statuses.RETRACTED
        latest_version = mailshot.last_version_for_ref == mailshot.version

        return retracted and latest_version

    def get_context_data(self, obj: Mailshot, csrf_token: str, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(obj, csrf_token, **kwargs)
        context["action"] = reverse("mailshot-republish", kwargs={"mailshot_pk": obj.pk})

        return context
