from django.contrib import messages
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe

from web.domains.template.models import Template
from web.models.mixins import Archivable


class ListAction:
    def __init__(self, inline=False, icon_only=False):
        self.inline = inline
        self.icon_only = icon_only

    def _get_item(self, request, model):
        _id = request.POST.get("item")
        return get_object_or_404(model, pk=_id)

    def display(self, object):
        return True


class PostAction(ListAction):
    template = "model/actions/submit.html"
    template_inline = "model/actions/submit-inline.html"

    # Overridden in child classes
    action = "unset"
    label = "unset"

    confirm = True  # confirm action before submitting

    def as_html(self, object, csrf_token, **kwargs):
        return mark_safe(
            render_to_string(
                self.template_inline if self.inline else self.template,
                self.get_context_data(object, csrf_token, **kwargs),
            )
        )

    def get_context_data(self, object, csrf_token, **kwargs):
        return {
            "icon": getattr(self, "icon", None),
            "csrf_token": csrf_token,
            "object": object,
            "confirm": self.confirm,
            "confirm_message": getattr(self, "confirm_message", None),
            "action": self.action,
            "label": self.label,
            "icon_only": self.icon_only,
        }

    def handle(self, request, view, *args, **kwargs):
        raise SuspiciousOperation("Not implemented!")


class LinkAction(ListAction):
    template = "model/actions/link.html"
    template_inline = "model/actions/link-inline.html"

    # Overridden in child classes
    icon = "unset"
    label = "unset"

    def href(self, object):
        return f"{object.id}/"

    def as_html(self, object, *args, **kwargs):
        return mark_safe(
            render_to_string(
                self.template_inline if self.inline else self.template,
                self.get_context_data(object),
            )
        )

    def get_context_data(self, object):
        return {
            "icon": self.icon or None,
            "object": object,
            "label": self.label,
            "href": self.href(object),
            "icon_only": self.icon_only,
        }


# note that this seems to be unused, and web/templates/tables/tables.html (lines
# 27-28) hardcodes the view-link generation
class View(LinkAction):
    label = "View"
    icon = "icon-eye"


class Edit(LinkAction):
    label = "Edit"
    icon = "icon-pencil"

    def href(self, object):
        return f"{object.id}/edit/"


class EditTemplate(LinkAction):
    label = "Edit"
    icon = "icon-pencil"

    def href(self, instance):
        # TODO: add CFS_SCHEDULE and point it its special URL
        if instance.template_type == Template.CFS_DECLARATION_TRANSLATION:
            return reverse("template-cfs-declaration-translation-edit", kwargs={"pk": instance.pk})
        elif instance.template_type == Template.CFS_SCHEDULE_TRANSLATION:
            return reverse("template-cfs-schedule-translation-edit", kwargs={"pk": instance.pk})

        return f"{instance.id}/edit/"


class Archive(PostAction):
    action = "archive"
    label = "Archive"
    confirm_message = "Are you sure you want to archive this record?"
    icon = "icon-bin"

    def display(self, object):
        return isinstance(object, Archivable) and object.is_active

    def handle(self, request, view):
        self._get_item(request, view.model).archive()
        messages.success(request, "Record archived successfully")


class Unarchive(PostAction):
    action = "unarchive"
    label = "Unarchive"
    confirm_message = "Are you sure you want to unarchive this record?"
    icon = "icon-undo2"

    def display(self, object):
        return isinstance(object, Archivable) and not object.is_active

    def handle(self, request, view):
        # TODO: unarchive can be blocked, this function should probably return
        # an error string if it fails?
        self._get_item(request, view.model).unarchive()
        messages.success(request, "Record restored successfully")


class CreateIndividualAgent(LinkAction):
    label = "Create Individual Agent"
    icon = "icon-user-plus"

    def href(self, object):
        return reverse(
            "importer-agent-create", kwargs={"importer_pk": object.pk, "entity": "individual"}
        )


class CreateOrganisationAgent(LinkAction):
    label = "Create Organisation Agent"
    icon = "icon-user-plus"

    def href(self, object):
        return reverse(
            "importer-agent-create", kwargs={"importer_pk": object.pk, "entity": "organisation"}
        )


class CreateExporterAgent(LinkAction):
    label = "Create Agent"
    icon = "icon-user-plus"

    def href(self, object):
        return reverse("exporter-agent-create", kwargs={"exporter_pk": object.pk})
