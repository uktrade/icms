from dataclasses import dataclass, field
from typing import Any, Literal, NamedTuple
from typing import Type as T
from typing import Union

from django.db.models import Model

from data_migration import models as dm
from web import models as web

ModelT = Union[T[Model], list[T[Model]]]
Anno = dict[str, Any] | None
Val = list[str] | None
Params = dict[str, int | str | bool | tuple]
Ref = Literal["access", "export", "import", "mailshot"]


@dataclass(frozen=True)
class QueryModel:
    query: str
    query_name: str
    model: Model
    parameters: Params = field(default_factory=dict)
    limit_by_field: str = "secure_lob_ref_id"


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
class CheckModel:
    name: str
    model_a: ModelT
    model_b: ModelT
    filter_params_a: Params = field(default_factory=dict)
    filter_params_b: Params = field(default_factory=dict)


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


@dataclass
class CheckFileQuery:
    name: str
    query_model: QueryModel
    model: ModelT
    filter_params: Params = field(default_factory=dict)
    exclude_params: Params = field(default_factory=dict)
    adjustment: int = 0

    @property
    def query(self) -> str:
        return (
            f"WITH DOC_QUERY AS ({self.query_model.query}) SELECT count(1) as count FROM DOC_QUERY"
        )

    @property
    def bind_vars(self) -> Params:
        return self.query_model.parameters

    @property
    def path_prefix(self) -> str:
        return str(self.query_model.parameters.get("path_prefix", ""))


@dataclass
class ModelReference:
    model: Model
    filter_params: Params = field(default_factory=dict)
    year: bool = True


def source_target_list(lst: list[str]) -> list[SourceTarget]:
    return [SourceTarget(getattr(dm, model_name), getattr(web, model_name)) for model_name in lst]
