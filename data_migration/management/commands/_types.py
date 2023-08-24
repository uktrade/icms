from dataclasses import dataclass, field
from typing import Any, NamedTuple
from typing import Type as T
from typing import Union

from django.db.models import Model

from data_migration import models as dm
from web import models as web

ModelT = Union[T[Model], list[T[Model]]]
Anno = dict[str, Any] | None
Val = list[str] | None
Params = dict[str, int | str | bool | tuple]


@dataclass(frozen=True)
class QueryModel:
    query: str
    query_name: str
    model: Model
    parameters: Params = field(default_factory=dict)


class SourceTarget(NamedTuple):
    source: Model
    target: Model


class M2M(NamedTuple):
    source: Model
    target: Model
    field: str


@dataclass(frozen=True)
class CheckCount:
    name: str
    expected_count: int
    model: ModelT
    filter_params: Params = field(default_factory=dict)
    annotation: Anno = None
    values: Val = None


@dataclass(frozen=True)
class CheckQuery:
    name: str
    query: str
    model: ModelT
    filter_params: Params = field(default_factory=dict)
    exclude_params: Params = field(default_factory=dict)
    bind_vars: Params = field(default_factory=dict)
    adjustment: int = 0
    note: str = ""


def source_target_list(lst: list[str]):
    return [SourceTarget(getattr(dm, model_name), getattr(web, model_name)) for model_name in lst]
