from typing import Any

from django.http import HttpRequest

from web.domains.case.services import document_pack
from web.models import ImportApplication


def get_active_licence_reference(application: ImportApplication) -> str:
    pack = document_pack.pack_active_get_optional(application)

    if not pack:
        return ""

    licence = document_pack.doc_ref_licence_get_optional(pack)

    return licence.reference if licence else ""


def case(request: HttpRequest) -> dict[str, Any]:
    """Return context variables / functions relating to a case."""

    return {
        "get_active_licence_reference": get_active_licence_reference,
    }
