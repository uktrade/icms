from typing import TYPE_CHECKING, List, NamedTuple, Optional, Tuple, Type, Union

from web.domains.file.models import File
from web.models import (
    AccessRequest,
    CertificateOfFreeSaleApplication,
    DerogationsApplication,
    DFLApplication,
    ExportApplication,
    ImportApplication,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    TextilesApplication,
    WoodQuotaApplication,
)

if TYPE_CHECKING:
    from django.db.models import QuerySet

ImpOrExp = Union[ImportApplication, ExportApplication]
ImpOrExpT = Type[ImpOrExp]

ImpOrExpOrAccess = Union[ImportApplication, ExportApplication, AccessRequest]
ImpOrExpOrAccessT = Type[ImpOrExpOrAccess]


ApplicationsWithChecklist = Union[
    OpenIndividualLicenceApplication,
    DFLApplication,
    SILApplication,
    WoodQuotaApplication,
    DerogationsApplication,
    OutwardProcessingTradeApplication,
    TextilesApplication,
]

ApplicationsWithCaseEmail = Union[
    OpenIndividualLicenceApplication,
    DFLApplication,
    SILApplication,
    SanctionsAndAdhocApplication,
    CertificateOfFreeSaleApplication,
]


class CaseEmailConfig(NamedTuple):
    application: ApplicationsWithCaseEmail
    to_choices: Optional[List[Tuple[str, str]]]
    file_qs: "QuerySet[File]"
