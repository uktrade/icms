from typing import Literal

from django.db.models import Model

from data_migration import models as dm
from data_migration.management.commands._types import M2M, QueryModel, SourceTarget
from data_migration.models import task
from data_migration.utils import xml_parser

from .export_application import (
    export_m2m,
    export_query_model,
    export_source_target,
    export_xml,
)
from .import_application import ia_m2m, ia_query_model, ia_source_target, ia_xml
from .reference import ref_m2m, ref_query_model, ref_source_target
from .user import user_m2m, user_query_model, user_source_target, user_xml

DATA_TYPE = Literal["reference", "import_application", "user", "file", "export_application"]

DATA_TYPE_QUERY_MODEL: dict[str, list[QueryModel]] = {
    "export_application": export_query_model,
    "file": [],
    "import_application": ia_query_model,
    "reference": ref_query_model,
    "user": user_query_model,
}

DATA_TYPE_SOURCE_TARGET: dict[str, list[SourceTarget]] = {
    "export_application": export_source_target,
    "file": [],
    "import_application": ia_source_target,
    "reference": ref_source_target,
    "user": user_source_target,
}

DATA_TYPE_M2M: dict[str, list[M2M]] = {
    "export_application": export_m2m,
    "import_application": ia_m2m,
    "reference": ref_m2m,
    "user": user_m2m,
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

FILE_MODELS: list[type[Model]] = [dm.FileFolder, dm.FileTarget, dm.DocFolder, dm.File]


TIMESTAMP_UPDATES: list[type[Model]] = [
    dm.ApprovalRequest,
    dm.CFSSchedule,
    dm.CaseNote,
    dm.Commodity,
    dm.CommodityGroup,
    dm.ExportApplicationCertificate,
    dm.File,
    dm.FurtherInformationRequest,
    dm.ImportApplication,
    dm.ImportApplicationLicence,
    dm.ImportContact,
    dm.Mailshot,
    dm.Process,
    dm.Section5Clause,
    dm.Template,
    dm.VariationRequest,
]

# TODO ICMSLST-1832 EndorsementImportApplication - check if needed in V2
# TODO ICMSLST-1832 WithdrawApplication
# TODO ICMSLST-1833 CertificateApplicationTemplate
