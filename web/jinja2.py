import re
from datetime import datetime
from typing import TYPE_CHECKING

import pytz
from compressor.contrib.jinja2ext import CompressorExtension
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models import Model
from django.http import HttpRequest
from django.urls import reverse
from django.utils.formats import get_format
from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import get_perms_for_model
from jinja2 import Environment, pass_eval_context
from markupsafe import Markup, escape

from web.domains.case.services import case_progress
from web.domains.case.types import ImpOrExp
from web.domains.workbasket.actions.ilb_admin_actions import TakeOwnershipAction
from web.menu import Menu
from web.types import AuthenticatedHttpRequest

if TYPE_CHECKING:
    from web.models import User


@pass_eval_context
def nl2br(eval_ctx, value):
    paragraph_re = re.compile(r"(?:\r\n|\r|\n){2,}")
    paragraphs = paragraph_re.split(escape(value))
    html = ("<p>{}</p>".format(p.replace("\n", Markup("<br>\n"))) for p in paragraphs)
    result = "\n\n".join(html)
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def show_all_attrs(value):
    res = []
    for k in dir(value):
        res.append(f"{k!r} {getattr(value, k)!r}\n")
    return "\n".join(res)


def input_datetime(value):
    """
    Convert a utc datetime from string to input date format
    """
    if not value:
        return ""

    input_formats = get_format("DATETIME_INPUT_FORMATS")
    for format in input_formats:
        try:
            datetime.strptime(value, format)
            return value
        except ValueError:
            continue

    local_timezone = pytz.timezone(settings.TIME_ZONE)
    naive_datetime = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
    local_datetime = local_timezone.localize(naive_datetime, is_dst=None)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    for format in get_format("DATETIME_INPUT_FORMATS"):
        try:
            return utc_datetime.strftime(format)
        except (ValueError, TypeError):
            continue

    return value


def modify_query(request, **new_params):
    params = request.GET.copy()
    for k, v in new_params.items():
        params[k] = v
    return request.build_absolute_uri("?" + params.urlencode())


def icms_link(request: HttpRequest, url: str, link_text: str, target: str = "_self") -> str:
    # TODO: might have to enhance this to strip out path components after "#" from both urls
    class_attr = "current-page" if request.path == url else ""

    return Markup(
        f'<li class="{class_attr}"><a href="{url}" target={target}>{escape(link_text)}</a></li>'
    )


def menu(request):
    return Menu().as_html(request)


def verbose_name(obj: Model, field_name: str) -> str:
    field = obj._meta.get_field(field_name)
    return getattr(field, "verbose_name", field.name)


def show_optional_label(bound: forms.BoundField, show_optional: bool) -> bool:
    """Used in icms/web/templates/forms/fields.html to show the optional label.

    :param bound: The bound form field
    :param show_optional: Set in template - defaults to true
    :return: True if optional label should be shown
    """

    form = bound.form
    field = bound.field

    # OptionalFormMixin attribute.
    required_fields: list[str] = getattr(form, "required_fields", [])

    if show_optional and not field.required and bound.name not in required_fields:
        return True

    return False


def show_take_ownership_url(
    request: AuthenticatedHttpRequest, application: ImpOrExp, case_type: str
) -> bool:
    if case_type not in ["import", "export"]:
        return False

    user = request.user

    action = TakeOwnershipAction(
        user=user,
        case_type=case_type,
        application=application,
        tasks=case_progress.get_active_task_list(application),
        is_ilb_admin=user.has_perm("web.ilb_admin"),
        is_importer_user=user.has_perm("web.importer_access"),
        # Set to False as checking is_rejected isn't required for TakeOwnershipAction
        is_rejected=False,
    )

    return action.show_link()


def get_latest_issued_document(application):
    """Used to get the active document pack in one template"""

    from web.domains.case.services import document_pack

    return document_pack.pack_active_get(application)


def get_active_task_list(application):
    """Used to case the active task list in one template macro."""

    return case_progress.get_active_task_list(application)


def get_user_obj_perms(user: "User") -> ObjectPermissionChecker:
    """Return a ObjectPermissionChecker initialised for the supplied user."""

    checker = ObjectPermissionChecker(user)

    return checker


# TODO: Decide if we want to do this or supply as a list from the view
def get_model_perms(model_cls_or_instance) -> list[tuple[str, str]]:
    model_perms = get_perms_for_model(model_cls_or_instance)

    return [(perm.codename, perm.name) for perm in model_perms]


def environment(**options):
    env = Environment(extensions=[CompressorExtension], **options)
    env.globals.update(
        {
            "static": staticfiles_storage.url,
            "icms_url": reverse,
            "icms_link": icms_link,
            "get_messages": messages.get_messages,
            "modify_query": modify_query,
            "menu": menu,
            "show_optional_label": show_optional_label,
            # Reuse the workbasket logic to show url.
            "show_take_ownership_url": show_take_ownership_url,
            "get_latest_issued_document": get_latest_issued_document,
            "get_active_task_list": get_active_task_list,
            "get_user_obj_perms": get_user_obj_perms,
            "get_model_perms": get_model_perms,
        }
    )
    env.filters["show_all_attrs"] = show_all_attrs
    env.filters["input_datetime"] = input_datetime
    env.filters["nl2br"] = nl2br
    env.filters["verbose_name"] = verbose_name

    return env
