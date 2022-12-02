from typing import TYPE_CHECKING, NamedTuple, Union

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
    ExportApplicationCertificate,
    ExportApplicationType,
    ImportApplication,
    ImportApplicationLicence,
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
ImpOrExpT = type[ImpOrExp]

ImpOrExpOrAccess = Union[ImportApplication, ExportApplication, AccessRequest]
ImpOrExpOrAccessT = type[ImpOrExpOrAccess]


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

IssuedDocument = Union[ImportApplicationLicence, ExportApplicationCertificate]


class CaseEmailConfig(NamedTuple):
    application: ApplicationsWithCaseEmail
    file_qs: "QuerySet[File]"
    to_choices: list[tuple[str, str]] | None = None
