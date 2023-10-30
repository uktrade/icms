from collections.abc import Collection

from django.conf import settings
from django.template.loader import render_to_string

from web.models import File
from web.sites import get_caseworker_site_domain
from web.utils.s3 import get_file_from_s3, get_s3_client


def render_email(template, context):
    """Adds shared variables into context and renders the email"""
    context = context or {}
    # TODO: ICMSLST-2313 Revisit (render_email used in 5 places)
    context["url"] = get_caseworker_site_domain()
    context["contact_email"] = settings.ILB_CONTACT_EMAIL
    context["contact_phone"] = settings.ILB_CONTACT_PHONE
    return render_to_string(template, context)


def get_attachments(file_ids: Collection[int]) -> Collection[tuple[str, bytes]]:
    if not file_ids:
        return []

    attachments = []
    files = File.objects.filter(pk__in=file_ids).values("path", "filename").order_by("pk")
    s3_client = get_s3_client()

    for f in files:
        file_content = get_file_from_s3(f["path"], client=s3_client)
        attachments.append((f["filename"], file_content))

    return attachments
