from typing import NamedTuple, TypeAlias, Union

from django.db.models import QuerySet

from web.models import (
    CaseEmailDownloadLink,
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    ConstabularyLicenceDownloadLink,
    DerogationsApplication,
    DFLApplication,
    ExportApplication,
    ExportApplicationCertificate,
    ExportApplicationType,
    Exporter,
    ExporterAccessRequest,
    ExporterApprovalRequest,
    File,
    FirearmsAuthority,
    ImportApplication,
    ImportApplicationLicence,
    ImportApplicationType,
    Importer,
    ImporterAccessRequest,
    ImporterApprovalRequest,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    SanctionsAndAdhocApplication,
    Section5Authority,
    SILApplication,
    TextilesApplication,
    WoodQuotaApplication,
)

Organisation = Union[Importer, Exporter]
Authority = Union[FirearmsAuthority, Section5Authority]

ImpTypeOrExpType = Union[ImportApplicationType, ExportApplicationType]

ImpOrExp = Union[ImportApplication, ExportApplication]
ImpAccessOrExpAccess = Union[ImporterAccessRequest, ExporterAccessRequest]

ImpOrExpT = type[ImpOrExp]

ImpOrExpOrAccess = Union[
    ImportApplication, ExportApplication, ImporterAccessRequest, ExporterAccessRequest
]
ImpOrExpOrAccessT = type[ImpOrExpOrAccess]

ImpOrExpApproval = Union[ImporterApprovalRequest, ExporterApprovalRequest]

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

DownloadLink = Union[ConstabularyLicenceDownloadLink, CaseEmailDownloadLink]


CaseDocumentsMetadata: TypeAlias = dict[int, dict[str, str]]


class CaseEmailConfig(NamedTuple):
    application: ApplicationsWithCaseEmail
    file_qs: QuerySet[File]
    file_metadata: CaseDocumentsMetadata
    to_choices: list[tuple[str, str]] | None = None
