import enum
import sys
from typing import Any

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
class _PermissionTextChoiceMeta(ChoicesMeta):
    names: list[str]
    choices: list[tuple[str, str]]
    labels: list[str]
    values: list[str]

class PermissionTextChoice(str, Choices, metaclass=_PermissionTextChoiceMeta):
    @enum_property
    def value(self) -> str: ...
    @enum_property
    def codename(self) -> str: ...
    @classmethod
    def get_permissions(cls) -> list[tuple[str, str]]: ...
    @staticmethod
    def _remove_prefix(v: tuple[str, str]) -> tuple[str, str]: ...
