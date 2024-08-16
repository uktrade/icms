import base64
import datetime as dt
import re
from typing import TYPE_CHECKING

from compressor.contrib.jinja2ext import CompressorExtension
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models import Model
from django.http import HttpRequest
from django.urls import reverse
from django.utils import formats, timezone
from guardian.core import ObjectPermissionChecker
from jinja2 import Environment, pass_eval_context
from markupsafe import Markup, escape

from web.domains.case.services import case_progress
from web.domains.case.types import ImpOrExp
from web.domains.workbasket.actions import ActionConfig
from web.domains.workbasket.actions.ilb_admin_actions import TakeOwnershipAction
from web.menu import Menu
from web.permissions import Perms
from web.permissions.context_processors import UserObjectPerms
from web.types import AuthenticatedHttpRequest
from web.utils.sentry import capture_exception, capture_message

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


def modify_query(request, **new_params):
    params = request.GET.copy()
    for k, v in new_params.items():
        params[k] = v
    return request.build_absolute_uri("?" + params.urlencode())


def icms_link(request: HttpRequest, url: str, link_text: str, target: str = "_self") -> str:
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

    application.active_tasks = case_progress.get_active_task_list(application)

    config = ActionConfig(user=user, case_type=case_type, application=application)
    action = TakeOwnershipAction.from_config(config)

    return action.show_link()


def get_view_case_url(request: AuthenticatedHttpRequest, case_type: str, app_pk: int) -> str:
    """Used to retrieve the correct view case url based on the user permissions."""

    kwargs = {"application_pk": app_pk, "case_type": case_type}

    if request.user.has_perm(Perms.sys.ilb_admin):
        return reverse("case:manage", kwargs={"application_pk": app_pk, "case_type": case_type})
    else:
        return reverse("case:view", kwargs=kwargs)


def get_latest_issued_document(application):
    """Used to get the active document pack in one template"""

    from web.domains.case.services import document_pack

    return document_pack.pack_active_get(application)


def get_active_task_list(application):
    """Used to case the active task list in one template macro."""

    return case_progress.get_active_task_list(application)


def get_user_obj_perms(user: "User") -> ObjectPermissionChecker:
    """Return a ObjectPermissionChecker initialised for the supplied user."""
    checker = UserObjectPerms(user)

    return checker


def datetime_format(
    value: dt.datetime, _format: str = "%d-%b-%Y %H:%M:%S", local: bool = True
) -> str:
    """Format a datetime.datetime instance to the supplied format.

    Does the following:
      - Convert a timezone aware datetime in to the localtime.
      - Return the datetime formatted by the supplied format.

    The value is converted to the local timezone unless local is False.
    """

    if local:
        try:
            if isinstance(value, dt.datetime):
                value = timezone.localtime(value)
            else:
                capture_message(f"Tried to use datetime_format with: {value}")
        except ValueError:
            # Capture errors where a naive datetime is being used.
            # We should fix any naive datetime instances as ICMS defines USE_TZ = True
            capture_exception()

    return value.strftime(_format)


def environment(**options):
    # string_if_invalid is removed as it is not available as an option within the jinja environment
    # https://github.com/pytest-dev/pytest-django/issues/327
    options.pop("string_if_invalid", None)

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
            "get_view_case_url": get_view_case_url,
            "get_latest_issued_document": get_latest_issued_document,
            "get_active_task_list": get_active_task_list,
            "get_user_obj_perms": get_user_obj_perms,
            "get_css_rules_as_string": get_css_rules_as_string,
            "get_file_base64": get_file_base64,
            "gtm_enabled": settings.GTM_ENABLED,
            "get_gtm_container_id": get_gtm_container_id,
            "app_env": settings.APP_ENV,
        }
    )
    env.filters["nl2br"] = nl2br
    env.filters["verbose_name"] = verbose_name
    # Convert the timezone aware datetime in to the local format
    env.filters["localize"] = formats.localize
    # Convert the timezone aware datetime in to the localtime
    env.filters["localtime"] = timezone.template_localtime
    # Convert an aware datetime to local time and return the value's date.
    env.filters["localdate"] = timezone.localdate
    env.filters["datetime_format"] = datetime_format

    return env


def get_css_rules_as_string(path: str) -> str:
    """Get the css rules as a string from the supplied path."""
    css_file_path = settings.STATIC_ROOT / path
    return css_file_path.read_text()


def get_file_base64(path: str) -> str:
    """Get the file as a base64 string from the supplied path."""
    file_path = settings.STATIC_ROOT / path
    return base64.b64encode(file_path.read_bytes()).decode("utf-8")  # /PS-IGNORE


def get_gtm_container_id(request: AuthenticatedHttpRequest) -> str:
    current_site = request.site
    return settings.GTM_CONTAINER_IDS[current_site.name]
