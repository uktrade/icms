from web.domains.case._import.derogations.models import (
    DerogationsApplication,
    DerogationsChecklist,
)
from web.domains.case._import.fa.models import ImportContact, UserImportCertificate
from web.domains.case._import.fa_dfl.models import (
    DFLApplication,
    DFLChecklist,
    DFLGoodsCertificate,
    DFLSupplementaryInfo,
    DFLSupplementaryReport,
    DFLSupplementaryReportFirearm,
)
from web.domains.case._import.fa_oil.models import (
    ChecklistFirearmsOILApplication,
    OILSupplementaryInfo,
    OILSupplementaryReport,
    OILSupplementaryReportFirearm,
    OpenIndividualLicenceApplication,
)
from web.domains.case._import.fa_sil.models import (
    SILApplication,
    SILChecklist,
    SILGoodsSection1,
    SILGoodsSection2,
    SILGoodsSection5,
    SILGoodsSection582Obsolete,
    SILGoodsSection582Other,
    SILLegacyGoods,
    SILSupplementaryInfo,
    SILSupplementaryReport,
    SILSupplementaryReportFirearmSection1,
    SILSupplementaryReportFirearmSection2,
    SILSupplementaryReportFirearmSection5,
    SILSupplementaryReportFirearmSection582Obsolete,
    SILSupplementaryReportFirearmSection582Other,
    SILSupplementaryReportFirearmSectionLegacy,
    SILUserSection5,
)
from web.domains.case._import.ironsteel.models import (
    IronSteelApplication,
    IronSteelCertificateFile,
    IronSteelChecklist,
)
from web.domains.case._import.models import (
    ChiefRequestResponseErrors,
    ConstabularyLicenceDownloadLink,
    EndorsementImportApplication,
    ICMSHMRCChiefRequest,
    ImportApplication,
    ImportApplicationLicence,
    ImportApplicationType,
)
from web.domains.case._import.opt.models import (
    OPTChecklist,
    OutwardProcessingTradeApplication,
    OutwardProcessingTradeFile,
)
from web.domains.case._import.sanctions.models import (
    SanctionsAndAdhocApplication,
    SanctionsAndAdhocApplicationGoods,
)
from web.domains.case._import.sps.models import (
    PriorSurveillanceApplication,
    PriorSurveillanceContractFile,
)
from web.domains.case._import.textiles.models import (
    TextilesApplication,
    TextilesChecklist,
)
from web.domains.case._import.wood.models import (
    WoodContractFile,
    WoodQuotaApplication,
    WoodQuotaChecklist,
)
from web.domains.case.access.approval.models import (
    ApprovalRequest,
    ExporterApprovalRequest,
    ImporterApprovalRequest,
)
from web.domains.case.access.models import (
    AccessRequest,
    ExporterAccessRequest,
    ImporterAccessRequest,
)
from web.domains.case.export.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    CFSProduct,
    CFSProductActiveIngredient,
    CFSProductType,
    CFSSchedule,
    ExportApplication,
    ExportApplicationCertificate,
    ExportApplicationType,
    ExportCertificateCaseDocumentReferenceData,
    GMPFile,
)
from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.models import (
    CaseDocumentReference,
    CaseEmail,
    CaseEmailDownloadLink,
    CaseNote,
    UpdateRequest,
    VariationRequest,
    WithdrawApplication,
)
from web.domains.cat.models import (
    CertificateApplicationTemplate,
    CertificateOfFreeSaleApplicationTemplate,
    CertificateOfGoodManufacturingPracticeApplicationTemplate,
    CertificateOfManufactureApplicationTemplate,
    CFSProductActiveIngredientTemplate,
    CFSProductTemplate,
    CFSProductTypeTemplate,
    CFSScheduleTemplate,
)
from web.domains.commodity.models import (
    Commodity,
    CommodityGroup,
    CommodityType,
    Unit,
    Usage,
)
from web.domains.constabulary.models import Constabulary
from web.domains.country.models import (
    Country,
    CountryGroup,
    CountryTranslation,
    CountryTranslationSet,
    OverseasRegion,
)
from web.domains.exporter.models import (
    Exporter,
    ExporterContactInvite,
    ExporterGroupObjectPermission,
    ExporterUserObjectPermission,
)
from web.domains.file.models import File
from web.domains.firearms.models import (
    ActQuantity,
    FirearmsAct,
    FirearmsAuthority,
    ObsoleteCalibre,
    ObsoleteCalibreGroup,
)
from web.domains.importer.models import (
    Importer,
    ImporterContactInvite,
    ImporterGroupObjectPermission,
    ImporterUserObjectPermission,
)
from web.domains.legislation.models import ProductLegislation
from web.domains.mailshot.models import Mailshot
from web.domains.office.models import Office
from web.domains.sanction_email.models import SanctionEmail
from web.domains.section5.models import (
    ClauseQuantity,
    Section5Authority,
    Section5Clause,
)
from web.domains.sigl.models import SIGLTransmission
from web.domains.signature.models import Signature
from web.domains.template.models import CFSScheduleParagraph, Template, TemplateVersion
from web.domains.user.models import Email, PhoneNumber, User
from web.flow.models import Process, Task
from web.mail.models import EmailTemplate
from web.models.models import GlobalPermission, UniqueReference
from web.reports.models import GeneratedReport, Report, ScheduleReport

__all__ = [
    "AccessRequest",
    "ActQuantity",
    "ApprovalRequest",
    "CFSProduct",
    "CFSProductTemplate",
    "CFSProductActiveIngredient",
    "CFSProductActiveIngredientTemplate",
    "CFSProductType",
    "CFSProductTypeTemplate",
    "CFSSchedule",
    "CFSScheduleParagraph",
    "CFSScheduleTemplate",
    "CaseDocumentReference",
    "CaseEmail",
    "CaseEmailDownloadLink",
    "CaseNote",
    "CertificateApplicationTemplate",
    "CertificateOfFreeSaleApplication",
    "CertificateOfFreeSaleApplicationTemplate",
    "CertificateOfGoodManufacturingPracticeApplication",
    "CertificateOfGoodManufacturingPracticeApplicationTemplate",
    "CertificateOfManufactureApplication",
    "CertificateOfManufactureApplicationTemplate",
    "ChecklistFirearmsOILApplication",
    "ChiefRequestResponseErrors",
    "ClauseQuantity",
    "Commodity",
    "CommodityGroup",
    "CommodityType",
    "Constabulary",
    "Country",
    "CountryGroup",
    "CountryTranslation",
    "CountryTranslationSet",
    "DFLApplication",
    "DFLChecklist",
    "DFLGoodsCertificate",
    "DFLSupplementaryInfo",
    "DFLSupplementaryReport",
    "DFLSupplementaryReportFirearm",
    "DerogationsApplication",
    "DerogationsChecklist",
    "Email",
    "EmailTemplate",
    "EndorsementImportApplication",
    "ExportApplication",
    "ExportApplicationCertificate",
    "ExportApplicationType",
    "ExportCertificateCaseDocumentReferenceData",
    "Exporter",
    "ExporterAccessRequest",
    "ExporterApprovalRequest",
    "ExporterContactInvite",
    "ExporterGroupObjectPermission",
    "ExporterUserObjectPermission",
    "File",
    "FirearmsAct",
    "FirearmsAuthority",
    "FurtherInformationRequest",
    "GeneratedReport",
    "GMPFile",
    "GlobalPermission",
    "ICMSHMRCChiefRequest",
    "ImportApplication",
    "ConstabularyLicenceDownloadLink",
    "ImportApplicationLicence",
    "ImportApplicationType",
    "ImportContact",
    "Importer",
    "ImporterAccessRequest",
    "ImporterApprovalRequest",
    "ImporterContactInvite",
    "ImporterGroupObjectPermission",
    "ImporterUserObjectPermission",
    "IronSteelApplication",
    "IronSteelCertificateFile",
    "IronSteelChecklist",
    "Mailshot",
    "OILSupplementaryInfo",
    "OILSupplementaryReport",
    "OILSupplementaryReportFirearm",
    "OPTChecklist",
    "ObsoleteCalibre",
    "ObsoleteCalibreGroup",
    "Office",
    "OpenIndividualLicenceApplication",
    "OutwardProcessingTradeApplication",
    "OutwardProcessingTradeFile",
    "OverseasRegion",
    "PhoneNumber",
    "PriorSurveillanceApplication",
    "PriorSurveillanceContractFile",
    "Process",
    "ProductLegislation",
    "Report",
    "ScheduleReport",
    "SIGLTransmission",
    "SILApplication",
    "SILChecklist",
    "SILGoodsSection1",
    "SILGoodsSection2",
    "SILGoodsSection5",
    "SILGoodsSection582Obsolete",
    "SILGoodsSection582Other",
    "SILLegacyGoods",
    "SILSupplementaryInfo",
    "SILSupplementaryReport",
    "SILSupplementaryReportFirearmSection1",
    "SILSupplementaryReportFirearmSection2",
    "SILSupplementaryReportFirearmSection5",
    "SILSupplementaryReportFirearmSection582Obsolete",
    "SILSupplementaryReportFirearmSection582Other",
    "SILSupplementaryReportFirearmSectionLegacy",
    "SILUserSection5",
    "SanctionEmail",
    "SanctionsAndAdhocApplication",
    "SanctionsAndAdhocApplicationGoods",
    "Section5Authority",
    "Section5Clause",
    "Signature",
    "Task",
    "Template",
    "TemplateVersion",
    "TextilesApplication",
    "TextilesChecklist",
    "UniqueReference",
    "Unit",
    "UpdateRequest",
    "Usage",
    "User",
    "UserImportCertificate",
    "VariationRequest",
    "WithdrawApplication",
    "WoodContractFile",
    "WoodQuotaApplication",
    "WoodQuotaChecklist",
]
