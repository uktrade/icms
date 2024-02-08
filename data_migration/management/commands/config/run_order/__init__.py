from typing import Literal

from data_migration import queries
from data_migration.management.commands._types import M2M, QueryModel, SourceTarget
from data_migration.models import task
from data_migration.utils import xml_parser

from .export_application import (
    export_m2m,
    export_query_model,
    export_source_target,
    export_xml,
)
from .files import (
    file_folder_query_model,
    file_m2m,
    file_query_model,
    file_source_target,
)
from .import_application import ia_m2m, ia_query_model, ia_source_target, ia_xml
from .reference import ref_m2m, ref_query_model, ref_source_target
from .user import user_m2m, user_query_model, user_source_target, user_xml

DATA_TYPE = Literal[
    "reference", "import_application", "user", "file", "file_folder", "export_application"
]

DATA_TYPE_QUERY_MODEL: dict[str, list[QueryModel]] = {
    "export_application": export_query_model,
    "file": file_query_model,
    "file_folder": file_folder_query_model,
    "import_application": ia_query_model,
    "reference": ref_query_model,
    "user": user_query_model,
}

DATA_TYPE_SOURCE_TARGET: dict[str, list[SourceTarget]] = {
    "export_application": export_source_target,
    "file": file_source_target,
    "import_application": ia_source_target,
    "reference": ref_source_target,
    "user": user_source_target,
}

DATA_TYPE_M2M: dict[str, list[M2M]] = {
    "export_application": export_m2m,
    "import_application": ia_m2m,
    "reference": ref_m2m,
    "user": user_m2m,
    "file": file_m2m,
}

DATA_TYPE_XML: dict[str, list[type[xml_parser.BaseXmlParser]]] = {
    "export_application": export_xml,
    "import_application": ia_xml,
    "reference": [],
    "user": user_xml,
}

TASK_LIST = [
    task.PrepareTask,
    task.ProcessTask,
]


TIMESTAMP_UPDATES: list[str] = [
    queries.access_request_timestamp_update,
    queries.approval_request_timestamp_update,
    queries.cfs_schedule_timestamp_update,
    queries.case_note_created_timestamp_update,
    queries.commodity_timestamp_update,
    queries.commodity_group_timestamp_update,
    queries.export_certificate_timestamp_update,
    queries.file_timestamp_update,
    queries.fir_timestamp_update,
    queries.ia_timestamp_update,
    queries.ia_licence_timestamp_update,
    queries.import_contact_timestamp_update,
    queries.mailshot_timestamp_update,
    queries.process_timestamp_update,
    queries.section5_clause_timestamp_update,
    queries.template_timestamp_update,
    queries.variation_request_timestamp_update,
    queries.withdraw_application_timestamp_update,
]

# TODO ICMSLST-1832 EndorsementImportApplication - check if needed in V2
# TODO ICMSLST-1833 CertificateApplicationTemplate
