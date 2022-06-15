from types import ModuleType
from typing import NamedTuple

from django.db.models import Model

from data_migration import models as dm
from web import models as web

QueryModel = NamedTuple("QueryModel", [("module", ModuleType), ("query", str), ("model", Model)])
SourceTarget = NamedTuple("SourceTarget", [("source", Model), ("target", Model)])
M2M = NamedTuple("M2M", [("source", Model), ("target", Model), ("field", str)])


def source_target_list(lst: list[str]):
    return [SourceTarget(getattr(dm, model_name), getattr(web, model_name)) for model_name in lst]
