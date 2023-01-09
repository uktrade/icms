from typing import NamedTuple

from django.db.models import Model

from data_migration import models as dm
from web import models as web


class QueryModel(NamedTuple):
    query: str
    query_name: str
    model: Model


class SourceTarget(NamedTuple):
    source: Model
    target: Model


class M2M(NamedTuple):
    source: Model
    target: Model
    field: str


def source_target_list(lst: list[str]):
    return [SourceTarget(getattr(dm, model_name), getattr(web, model_name)) for model_name in lst]
