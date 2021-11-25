from typing import Any

from django.db import models
from django.db.models.functions import Coalesce


def get_order_by_datetime(case_type: str) -> Any:
    if case_type == "import":
        return models.F("submit_datetime")
    else:
        return Coalesce("submit_datetime", "created")
