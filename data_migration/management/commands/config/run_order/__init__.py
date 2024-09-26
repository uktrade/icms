from typing import Literal

from data_migration.management.commands.types import M2M, QueryModel, SourceTarget
from data_migration.utils import xml_parser

from .files import file_query_model

DATA_TYPE = Literal[
    "reference", "import_application", "user", "file", "file_folder", "export_application"
]

DATA_TYPE_QUERY_MODEL: dict[str, list[QueryModel]] = {
    "file": file_query_model,
}

DATA_TYPE_SOURCE_TARGET: dict[str, list[SourceTarget]] = {}

DATA_TYPE_M2M: dict[str, list[M2M]] = {}

DATA_TYPE_XML: dict[str, list[type[xml_parser.BaseXmlParser]]] = {}

TASK_LIST = []


TIMESTAMP_UPDATES: list[str] = []
