from typing import TYPE_CHECKING, List, NamedTuple, Optional, Tuple, Type, Union

from web.domains.case._import.ironsteel.models import IronSteelApplication
from web.domains.case.export.models import (
    CertificateOfGoodManufacturingPracticeApplication,
)
from web.domains.file.models import File
from web.models import (
    AccessRequest,
    CertificateOfFreeSaleApplication,
    DerogationsApplication,
    DFLApplication,
    ExportApplication,
    ExportApplicationType,
    ImportApplication,
    ImportApplicationType,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    TextilesApplication,
    WoodQuotaApplication,
)

if TYPE_CHECKING:
    from django.db.models import QuerySet

ImpTypeOrExpType = Union[ImportApplicationType, ExportApplicationType]

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
    IronSteelApplication,
]

ApplicationsWithCaseEmail = Union[
    OpenIndividualLicenceApplication,
    DFLApplication,
    SILApplication,
    SanctionsAndAdhocApplication,
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
]


class CaseEmailConfig(NamedTuple):
    application: ApplicationsWithCaseEmail
    file_qs: "QuerySet[File]"
    to_choices: Optional[List[Tuple[str, str]]] = None
