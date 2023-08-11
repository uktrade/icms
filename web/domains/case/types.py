from typing import NamedTuple, Union

from django.db.models import QuerySet

from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    DerogationsApplication,
    DFLApplication,
    ExportApplication,
    ExportApplicationCertificate,
    ExportApplicationType,
    ExporterAccessRequest,
    ExporterApprovalRequest,
    File,
    ImportApplication,
    ImportApplicationLicence,
    ImportApplicationType,
    ImporterAccessRequest,
    ImporterApprovalRequest,
    IronSteelApplication,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    TextilesApplication,
    WoodQuotaApplication,
)

ImpTypeOrExpType = Union[ImportApplicationType, ExportApplicationType]

ImpOrExp = Union[ImportApplication, ExportApplication]
ImpAccessOrExpAccess = Union[ImporterAccessRequest, ExporterAccessRequest]

ImpOrExpT = type[ImpOrExp]

ImpOrExpOrAccess = Union[
    ImportApplication, ExportApplication, ImporterAccessRequest, ExporterAccessRequest
]
ImpOrExpOrAccessT = type[ImpOrExpOrAccess]


ImpOrExpOrAccessOrApproval = Union[
    ImportApplication,
    ExportApplication,
    ImporterAccessRequest,
    ExporterAccessRequest,
    ImporterApprovalRequest,
    ExporterApprovalRequest,
]
ImpOrExpOrAccessOrApprovalT = type[ImpOrExpOrAccessOrApproval]


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

DocumentPack = Union[ImportApplicationLicence, ExportApplicationCertificate]


class CaseEmailConfig(NamedTuple):
    application: ApplicationsWithCaseEmail
    file_qs: QuerySet[File]
    to_choices: list[tuple[str, str]] | None = None
