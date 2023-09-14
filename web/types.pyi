import enum
import sys
from enum import Enum
from typing import TYPE_CHECKING, Any

from _typeshed import Incomplete
from django.http import HttpRequest

if TYPE_CHECKING:
    from django.contrib.sites.models import Site

    from web.middleware.common import ICMSMiddlewareContext
    from web.models import User

if sys.version_info >= (3, 11):
    enum_property = enum.property
else:
    enum_property = property

class ChoicesMeta(enum.EnumMeta):
    names: list[str]
    choices: list[tuple[Any, str]]
    labels: list[str]
    values: list[Any]
    def __contains__(self, member: Any) -> bool: ...

class Choices(enum.Enum, metaclass=ChoicesMeta):
    @property
    def label(self) -> str: ...
    @enum_property
    def value(self) -> Any: ...

# fake
class _TypedTextChoicesMeta(ChoicesMeta):
    names: list[str]
    choices: list[tuple[str, str]]
    labels: list[str]
    values: list[str]

class TypedTextChoices(str, Choices, metaclass=_TypedTextChoicesMeta):
    @enum_property
    def value(self) -> str: ...
    @enum_property
    def codename(self) -> str: ...
    @classmethod
    def get_permissions(cls) -> list[tuple[str, str]]: ...
    @staticmethod
    def _remove_prefix(v: tuple[str, str]) -> tuple[str, str]: ...

class AuthenticatedHttpRequest(HttpRequest):
    user: "User"
    icms: "ICMSMiddlewareContext"
    site: "Site"

class DocumentTypes(Enum):
    LICENCE_PREVIEW: Incomplete
    LICENCE_PRE_SIGN: Incomplete
    LICENCE_SIGNED: Incomplete
    CERTIFICATE_PREVIEW: Incomplete
    CERTIFICATE_PRE_SIGN: Incomplete
    CERTIFICATE_SIGNED: Incomplete
    COVER_LETTER_PREVIEW: Incomplete
    COVER_LETTER_PRE_SIGN: Incomplete
    COVER_LETTER_SIGNED: Incomplete
