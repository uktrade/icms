from data_migration import models as dm
from data_migration import queries
from data_migration.management.commands.types import M2M, QueryModel, SourceTarget
from data_migration.utils import xml_parser
from web import models as web

export_query_model = [
    QueryModel(queries.product_legislation, "product_legislation", dm.ProductLegislation),
    QueryModel(
        queries.export_application_type, "export_application_type", dm.ExportApplicationType
    ),
    QueryModel(queries.com_application, "com_application", dm.CertificateOfManufactureApplication),
    QueryModel(
        queries.gmp_application,
        "gmp_application",
        dm.CertificateOfGoodManufacturingPracticeApplication,
    ),
    QueryModel(queries.cfs_application, "cfs_application", dm.CertificateOfFreeSaleApplication),
    QueryModel(queries.cfs_schedule, "cfs_schedule", dm.CFSSchedule),
    QueryModel(
        queries.export_application_countries,
        "export_application_countries",
        dm.ExportApplicationCountries,
    ),
    QueryModel(queries.export_certificate, "export_certificate", dm.ExportApplicationCertificate),
    QueryModel(
        queries.export_document_pack_acknowledged,
        "Export Document Pack Acknowledgement",
        dm.DocumentPackAcknowledgement,
    ),
    QueryModel(queries.beis_emails, "beis_emails", dm.CaseEmail),
    QueryModel(queries.hse_emails, "hse_emails", dm.CaseEmail),
]

export_source_target = [
    SourceTarget(dm.ProductLegislation, web.ProductLegislation),
    SourceTarget(dm.ExportApplicationType, web.ExportApplicationType),
    SourceTarget(dm.ExportApplication, web.ExportApplication),
    SourceTarget(dm.CertificateOfManufactureApplication, web.CertificateOfManufactureApplication),
    SourceTarget(
        dm.CertificateOfGoodManufacturingPracticeApplication,
        web.CertificateOfGoodManufacturingPracticeApplication,
    ),
    SourceTarget(dm.CertificateOfFreeSaleApplication, web.CertificateOfFreeSaleApplication),
    SourceTarget(dm.CFSSchedule, web.CFSSchedule),
    SourceTarget(dm.CFSProduct, web.CFSProduct),
    SourceTarget(dm.CFSProductType, web.CFSProductType),
    SourceTarget(dm.CFSProductActiveIngredient, web.CFSProductActiveIngredient),
    SourceTarget(dm.ExportApplicationCertificate, web.ExportApplicationCertificate),
    SourceTarget(dm.WithdrawApplication, web.WithdrawApplication),
]

export_m2m = [
    M2M(dm.VariationRequest, web.ExportApplication, "variation_requests"),
    M2M(dm.ExportApplicationCountries, web.ExportApplication, "countries"),
    M2M(dm.CFSLegislation, web.CFSSchedule, "legislations"),
    M2M(dm.CaseNote, web.ExportApplication, "case_notes"),
    M2M(dm.CaseEmail, web.ExportApplication, "case_emails"),
    M2M(dm.FurtherInformationRequest, web.ExportApplication, "further_information_requests"),
    M2M(dm.UpdateRequest, web.ExportApplication, "update_requests"),
    M2M(dm.DocumentPackAcknowledgement, web.ExportApplicationCertificate, "cleared_by"),
    M2M(dm.DocumentPackAcknowledgement, web.ExportApplication, "cleared_by"),
]

export_xml = [
    xml_parser.CFSLegislationParser,
    xml_parser.CFSProductParser,
    xml_parser.ProductTypeParser,
    xml_parser.ActiveIngredientParser,
    xml_parser.CaseNoteExportParser,
    xml_parser.FIRExportParser,
    xml_parser.UpdateExportParser,
    xml_parser.VariationExportParser,
    xml_parser.WithdrawalExportParser,
]
