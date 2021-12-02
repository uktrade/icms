from typing import Any

from django.db import models
from django.db.models.functions import Coalesce


def get_order_by_datetime(case_type: str) -> Any:
    if case_type == "import":
        return models.F("submit_datetime")
    else:
        return Coalesce("submit_datetime", "created")


# TODO: ICMSLST-1240 Add permission checks
# This function isn't correct but its a start
# def has_search_permission(user: User, imp_or_exp: str):
#     ilb_admin = user.has_perm("web.ilb_admin")
#     importer_user = user.has_perm("web.importer_access")
#     exporter_user = user.has_perm("web.exporter_access")
#
#     if imp_or_exp == "import":
#         return ilb_admin or importer_user
#     else:
#         return ilb_admin or exporter_user
