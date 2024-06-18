from django.db.models import Count

import web.models as web
from data_migration import queries
from data_migration.management.commands.config.run_order import files
from data_migration.management.commands.types import (
    CheckCount,
    CheckFileQuery,
    CheckModel,
    CheckQuery,
)
from web.flow.models import ProcessTypes

CHECK_DATA_COUNTS: list[CheckCount] = [
    CheckCount(
        name="Firearms Acts",
        expected_count=7,
        model=web.FirearmsAct,
    ),
    CheckCount(
        name="Section 5 Clauses",
        expected_count=17,
        model=web.Section5Clause,
    ),
    CheckCount(
        name="Import Applications Without Document Packs",
        expected_count=0,
        model=web.ImportApplication,
        filter_params={"licences__isnull": True, "submit_datetime__isnull": False},
    ),
    CheckCount(
        name="Export Applications Without Document Packs",
        expected_count=0,
        model=web.ExportApplication,
        filter_params={"certificates__isnull": True, "submit_datetime__isnull": False},
    ),
    CheckCount(
        name="Individual Importers Without User",
        expected_count=0,
        model=web.Importer,
        filter_params={"type": web.Importer.INDIVIDUAL, "user__isnull": True},
    ),
    CheckCount(
        name="Organisation Importers With User",
        expected_count=0,
        model=web.Importer,
        filter_params={"type": web.Importer.ORGANISATION, "user__isnull": False},
    ),
    CheckCount(
        name="Users With Multiple Groups",
        expected_count=16,
        model=web.User,
        filter_params={"group_count__gt": 1},
        annotation={"group_count": Count("groups")},
    ),
    CheckCount(
        name="Duplicate File Paths",
        expected_count=0,
        model=web.File,
        filter_params={"path_count__gt": 1},
        annotation={"path_count": Count("pk")},
        values=["path"],
    ),
    CheckCount(
        name="Countries all have regions",
        expected_count=0,
        model=web.Country,
        filter_params={"overseas_region__isnull": True, "type": web.Country.SOVEREIGN_TERRITORY},
    ),
    CheckCount(
        name="Countries",
        expected_count=269,
        model=web.Country,
    ),
    CheckCount(
        name="Countries that are active",
        expected_count=183,
        model=web.Country,
        filter_params={"is_active": True},
    ),
    CheckCount(
        name="All Submitted DFL Applications Have Goods Certificate",
        expected_count=0,
        model=web.DFLApplication,
        filter_params={"submit_datetime__isnull": False, "goods_certificates__isnull": True},
    ),
    CheckCount(
        name="All Submitted DFL Applications Have Constabulary",
        expected_count=0,
        model=web.DFLApplication,
        filter_params={"submit_datetime__isnull": False, "constabulary_id__isnull": True},
    ),
    CheckCount(
        name="All Submitted Sanctions Applications Have Goods",
        expected_count=0,
        model=web.SanctionsAndAdhocApplication,
        filter_params={"submit_datetime__isnull": False, "sanctions_goods__isnull": True},
    ),
    CheckCount(
        name="Active country translation sets",
        expected_count=5,
        model=web.CountryTranslationSet,
        filter_params={"is_active": True},
    ),
    CheckCount(
        name="Missing French country translations",
        expected_count=0,
        model=web.Country,
        exclude_params={
            "id__in": web.CountryTranslation.objects.filter(
                translation_set__name="French"
            ).values_list("country_id")
        },
    ),
    CheckCount(
        name="Missing Spanish country translations",
        expected_count=0,
        model=web.Country,
        exclude_params={
            "id__in": web.CountryTranslation.objects.filter(
                translation_set__name="Spanish"
            ).values_list("country_id")
        },
    ),
    CheckCount(
        name="Missing Russian country translations",
        expected_count=0,
        model=web.Country,
        exclude_params={
            "id__in": web.CountryTranslation.objects.filter(
                translation_set__name="Russian"
            ).values_list("country_id")
        },
    ),
    CheckCount(
        name="Missing Portuguese country translations",
        expected_count=0,
        model=web.Country,
        exclude_params={
            "id__in": web.CountryTranslation.objects.filter(
                translation_set__name="Portuguese"
            ).values_list("country_id")
        },
    ),
    CheckCount(
        name="Missing Turkish country translations",
        expected_count=0,
        model=web.Country,
        exclude_params={
            "id__in": web.CountryTranslation.objects.filter(
                translation_set__name="Turkish"
            ).values_list("country_id")
        },
    ),
]


CHECK_MODELS = [
    CheckModel(
        name="All Import Applications Have Unique Reference",
        model_a=web.ImportApplication,
        filter_params_a={},
        model_b=web.UniqueReference,
        filter_params_b={"prefix": web.UniqueReference.Prefix.IMPORT_APP},
    ),
    CheckModel(
        name="All Import Applications Licence Unique References Have FK",
        model_a=web.ImportApplication,
        filter_params_a={"licence_reference__isnull": False},
        model_b=web.UniqueReference,
        filter_params_b={"prefix": web.UniqueReference.Prefix.IMPORT_LICENCE_DOCUMENT},
    ),
    CheckModel(
        name="All CFS and COM Applications Have Unique Reference",
        model_a=web.ExportApplication,
        filter_params_a={"process_type__in": (ProcessTypes.CFS, ProcessTypes.COM)},
        model_b=web.UniqueReference,
        filter_params_b={"prefix": web.UniqueReference.Prefix.EXPORT_APP_CA},
    ),
    CheckModel(
        name="All GMP Applications Have Unique Reference",
        model_a=web.ExportApplication,
        filter_params_a={"process_type": ProcessTypes.GMP},
        model_b=web.UniqueReference,
        filter_params_b={"prefix": web.UniqueReference.Prefix.EXPORT_APP_GA},
    ),
    CheckModel(
        name="All Migrated Users Have Email Field",
        model_a=web.User,
        filter_params_a={"email__contains": "@"},
        model_b=web.User,
        filter_params_b={"pk__gt": 0},
    ),
]


CHECK_DATA_QUERIES: list[CheckQuery] = [
    CheckQuery(
        name="Country Group Countries",
        query=queries.country_group_countries_count,
        model=web.CountryGroup.countries.through,
    ),
    CheckQuery(
        name="DFL Goods Certificates",
        query=queries.fa_goods_certificate_count,
        model=web.DFLGoodsCertificate,
        bind_vars={"FA_TYPE": "DEACTIVATED"},
    ),
    CheckQuery(
        name="OIL User Import Certificates",
        query=queries.fa_goods_certificate_count,
        model=web.OpenIndividualLicenceApplication.user_imported_certificates.through,
        bind_vars={"FA_TYPE": "OIL"},
    ),
    CheckQuery(
        name="OIL Firearms Authority Certificates",
        query=queries.fa_firearms_authority_certificate_count,
        model=web.OpenIndividualLicenceApplication.verified_certificates.through,
        bind_vars={"FA_TYPE": "OIL"},
    ),
    CheckQuery(
        name="SIL User Import Certificates",
        query=queries.fa_goods_certificate_count,
        model=web.SILApplication.user_imported_certificates.through,
        bind_vars={"FA_TYPE": "SIL"},
        adjustment=2,
        note="Certficates without constabulary id or file upload are not migrated. See ICMSLST-1905",
    ),
    CheckQuery(
        name="SIL Firearms Authority Certificates",
        query=queries.fa_firearms_authority_certificate_count,
        model=web.SILApplication.verified_certificates.through,
        bind_vars={"FA_TYPE": "SIL"},
    ),
    CheckQuery(
        name="SIL Section 5 Authority Certificates",
        query=queries.sil_section_5_authority_certificate_count,
        model=web.SILApplication.verified_section5.through,
    ),
    CheckQuery(
        name="SIL Section 1 Goods",
        query=queries.sil_section_goods_count,
        model=web.SILGoodsSection1,
        bind_vars={"SECTION": "SEC1"},
    ),
    CheckQuery(
        name="SIL Section 2 Goods",
        query=queries.sil_section_goods_count,
        model=web.SILGoodsSection2,
        bind_vars={"SECTION": "SEC2"},
    ),
    CheckQuery(
        name="SIL Section 5 Goods",
        query=queries.sil_section_goods_count,
        model=web.SILGoodsSection5,
        bind_vars={"SECTION": "SEC5"},
    ),
    CheckQuery(
        name="SIL Section 5 - Obsolete Calibre Goods",
        query=queries.sil_section_goods_count,
        model=web.SILGoodsSection582Obsolete,  # /PS-IGNORE
        bind_vars={"SECTION": "OBSOLETE_CALIBRE"},
    ),
    CheckQuery(
        name="SIL Section 5 - Other Goods",
        query=queries.sil_section_goods_count,
        model=web.SILGoodsSection582Other,  # /PS-IGNORE
        bind_vars={"SECTION": "OTHER"},
    ),
    CheckQuery(
        name="SIL Legacy Goods",
        query=queries.sil_legacy_goods_count,
        model=web.SILLegacyGoods,
    ),
    CheckQuery(
        name="DFL Bought From Details",
        query=queries.fa_bought_from_count,
        model=web.ImportContact,
        filter_params={"import_application__process_type": ProcessTypes.FA_DFL},
        bind_vars={"FA_TYPE": "DEACTIVATED"},
    ),
    CheckQuery(
        name="OIL Bought From Details",
        query=queries.fa_bought_from_count,
        model=web.ImportContact,
        filter_params={"import_application__process_type": ProcessTypes.FA_OIL},
        bind_vars={"FA_TYPE": "OIL"},
    ),
    CheckQuery(
        name="SIL Bought From Details",
        query=queries.fa_bought_from_count,
        model=web.ImportContact,
        filter_params={"import_application__process_type": ProcessTypes.FA_SIL},
        bind_vars={"FA_TYPE": "SIL"},
    ),
    CheckQuery(
        name="DFL Supplementary Reports",
        query=queries.fa_supplementary_report_count,
        model=web.DFLSupplementaryReport,
        bind_vars={"FA_TYPE": "DEACTIVATED"},
    ),
    CheckQuery(
        name="DFL Supplementary Report Firearm Manual Details",
        query=queries.fa_supplementary_report_manual_count,
        model=web.DFLSupplementaryReportFirearm,
        filter_params={"is_manual": True},
        bind_vars={"FA_TYPE": "DEACTIVATED"},
    ),
    CheckQuery(
        name="DFL Supplementary Report Firearm Uploaded Documents",
        query=queries.fa_supplementary_report_upload_count,
        model=web.DFLSupplementaryReportFirearm,
        filter_params={"is_upload": True},
        bind_vars={"FA_TYPE": "DEACTIVATED"},
    ),
    CheckQuery(
        name="DFL Supplementary Report Firearm No Firearm",
        query=queries.fa_supplementary_report_no_firearm_count,
        model=web.DFLSupplementaryReportFirearm,
        filter_params={"is_no_firearm": True},
        bind_vars={"FA_TYPE": "DEACTIVATED"},
    ),
    CheckQuery(
        name="OIL Supplementary Reports",
        query=queries.fa_supplementary_report_count,
        model=web.OILSupplementaryReport,
        bind_vars={"FA_TYPE": "OIL"},
    ),
    CheckQuery(
        name="OIL Supplementary Report Firearm Manual Details",
        query=queries.fa_supplementary_report_manual_count,
        model=web.OILSupplementaryReportFirearm,
        filter_params={"is_manual": True},
        bind_vars={"FA_TYPE": "OIL"},
    ),
    CheckQuery(
        name="OIL Supplementary Report Firearm Uploaded Documents",
        query=queries.fa_supplementary_report_upload_count,
        model=web.OILSupplementaryReportFirearm,
        filter_params={"is_upload": True},
        bind_vars={"FA_TYPE": "OIL"},
    ),
    CheckQuery(
        name="OIL Supplementary Report Firearm No Firearm",
        query=queries.fa_supplementary_report_no_firearm_count,
        model=web.OILSupplementaryReportFirearm,
        filter_params={"is_no_firearm": True},
        bind_vars={"FA_TYPE": "OIL"},
    ),
    CheckQuery(
        name="SIL Supplementary Reports",
        query=queries.fa_supplementary_report_count,
        model=web.SILSupplementaryReport,
        filter_params={},
        bind_vars={"FA_TYPE": "SIL"},
    ),
    CheckQuery(
        name="SIL Supplementary Report Firearm Manual Details",
        query=queries.fa_supplementary_report_manual_count,
        model=[
            web.SILSupplementaryReportFirearmSection1,
            web.SILSupplementaryReportFirearmSection2,
            web.SILSupplementaryReportFirearmSection5,
            web.SILSupplementaryReportFirearmSection582Obsolete,  # /PS-IGNORE
            web.SILSupplementaryReportFirearmSection582Other,  # /PS-IGNORE
        ],
        filter_params={"is_manual": True},
        bind_vars={"FA_TYPE": "SIL"},
    ),
    CheckQuery(
        name="SIL Supplementary Report Firearm Uploaded Documents",
        query=queries.fa_supplementary_report_upload_count,
        model=[
            web.SILSupplementaryReportFirearmSection1,
            web.SILSupplementaryReportFirearmSection2,
            web.SILSupplementaryReportFirearmSection5,
            web.SILSupplementaryReportFirearmSection582Obsolete,  # /PS-IGNORE
            web.SILSupplementaryReportFirearmSection582Other,  # /PS-IGNORE
        ],
        filter_params={"is_upload": True},
        bind_vars={"FA_TYPE": "SIL"},
    ),
    CheckQuery(
        name="SIL Supplementary Report Firearm No Firearm",
        query=queries.fa_supplementary_report_no_firearm_count,
        model=[
            web.SILSupplementaryReportFirearmSection1,
            web.SILSupplementaryReportFirearmSection2,
            web.SILSupplementaryReportFirearmSection5,
            web.SILSupplementaryReportFirearmSection582Obsolete,  # /PS-IGNORE
            web.SILSupplementaryReportFirearmSection582Other,  # /PS-IGNORE
        ],
        filter_params={"is_no_firearm": True},
        bind_vars={"FA_TYPE": "SIL"},
        adjustment=1,
        note="Missing report data for one goods line in V1. See ICMSLST-1905",
    ),
    CheckQuery(
        name="Firearms Authority Act Quantity",
        query=queries.fa_authority_quantity_count,
        model=web.ActQuantity,
        bind_vars={"AUTHORITY_TYPE": "FIREARMS"},
    ),
    CheckQuery(
        name="Section 5 Authority Clause Quantity",
        query=queries.fa_authority_quantity_count,
        model=web.ClauseQuantity,
        bind_vars={"AUTHORITY_TYPE": "SECTION5"},
    ),
    CheckQuery(
        name="Sanctions Emails", query=queries.sanctions_email_count, model=web.SanctionEmail
    ),
    CheckQuery(
        name="CFS Products",
        query=queries.cfs_product_count,
        model=web.CFSProduct,
    ),
    CheckQuery(
        name="CFS Product Active Ingredients",
        query=queries.cfs_product_active_ingredient_count,
        model=web.CFSProductActiveIngredient,
    ),
    CheckQuery(
        name="CFS Product Type Numbers",
        query=queries.cfs_product_type_numbers_count,
        model=web.CFSProductType,
    ),
    CheckQuery(
        name="CFS Schedule Legislation",
        query=queries.cfs_schedule_legislation_count,
        model=web.CFSSchedule.legislations.through,
    ),
    CheckQuery(
        name="Variation Requests - DFL",
        query=queries.import_application_variation_count,
        model=web.VariationRequest,
        filter_params={"importapplication__process_type": ProcessTypes.FA_DFL},
        bind_vars={"IMA_TYPE": "FA", "IMA_SUB_TYPE": "DEACTIVATED"},
    ),
    CheckQuery(
        name="Variation Requests - OIL",
        query=queries.import_application_variation_count,
        model=web.VariationRequest,
        filter_params={"importapplication__process_type": ProcessTypes.FA_OIL},
        bind_vars={"IMA_TYPE": "FA", "IMA_SUB_TYPE": "OIL"},
    ),
    CheckQuery(
        name="Variation Requests - SIL",
        query=queries.import_application_variation_count,
        model=web.VariationRequest,
        filter_params={"importapplication__process_type": ProcessTypes.FA_SIL},
        bind_vars={"IMA_TYPE": "FA", "IMA_SUB_TYPE": "SIL"},
    ),
    CheckQuery(
        name="Variation Requests - Derogations",
        query=queries.import_application_variation_count,
        model=web.VariationRequest,
        filter_params={"importapplication__process_type": ProcessTypes.DEROGATIONS},
        bind_vars={"IMA_TYPE": "SAN", "IMA_SUB_TYPE": "SAN1"},
    ),
    CheckQuery(
        name="Variation Requests - OPT",
        query=queries.import_application_variation_count,
        model=web.VariationRequest,
        filter_params={"importapplication__process_type": ProcessTypes.OPT},
        bind_vars={"IMA_TYPE": "OPT", "IMA_SUB_TYPE": "QUOTA"},
    ),
    CheckQuery(
        name="Variation Requests - Sanctions and ADHOC",
        query=queries.import_application_variation_count,
        model=web.VariationRequest,
        filter_params={"importapplication__process_type": ProcessTypes.SANCTIONS},
        bind_vars={"IMA_TYPE": "ADHOC", "IMA_SUB_TYPE": "ADHOC1"},
    ),
    CheckQuery(
        name="Variation Requests - SPS",
        query=queries.import_application_variation_count,
        model=web.VariationRequest,
        filter_params={"importapplication__process_type": ProcessTypes.SPS},
        bind_vars={"IMA_TYPE": "SPS", "IMA_SUB_TYPE": "SPS1"},
    ),
    CheckQuery(
        name="Variation Requests - Textiles",
        query=queries.import_application_variation_count,
        model=web.VariationRequest,
        filter_params={"importapplication__process_type": ProcessTypes.TEXTILES},
        bind_vars={"IMA_TYPE": "TEX", "IMA_SUB_TYPE": "QUOTA"},
    ),
    CheckQuery(
        name="Variation Requests - Wood",
        query=queries.import_application_variation_count,
        model=web.VariationRequest,
        filter_params={"importapplication__process_type": ProcessTypes.WOOD},
        bind_vars={"IMA_TYPE": "WD", "IMA_SUB_TYPE": "QUOTA"},
    ),
    CheckQuery(
        name="Variation Requests - CFS",
        query=queries.export_application_variation_count,
        model=web.VariationRequest,
        filter_params={"exportapplication__process_type": ProcessTypes.CFS},
        bind_vars={"CA_TYPE": "CFS"},
    ),
    CheckQuery(
        name="Variation Requests - COM",
        query=queries.export_application_variation_count,
        model=web.VariationRequest,
        filter_params={"exportapplication__process_type": ProcessTypes.COM},
        bind_vars={"CA_TYPE": "COM"},
    ),
    CheckQuery(
        name="Variation Requests - GMP",
        query=queries.export_application_variation_count,
        model=web.VariationRequest,
        filter_params={"exportapplication__process_type": ProcessTypes.GMP},
        bind_vars={"CA_TYPE": "GMP"},
    ),
    CheckQuery(
        name="Templates",
        query=queries.template_count,
        model=web.Template,
        exclude_params={"application_domain": "UM"},
    ),
    CheckQuery(
        name="Template Countries",
        query=queries.template_country_count,
        model=web.Template.countries.through,
    ),
    CheckQuery(
        name="Template - CFS Schedule Paragraphs",
        query=queries.cfs_paragraph_count,
        model=web.CFSScheduleParagraph,
    ),
    CheckQuery(
        name="Template - Import Application Type Endorsements",
        query=queries.iat_endorsement_count,
        model=web.ImportApplicationType.endorsements.through,
    ),
    CheckQuery(
        name="ILB Case Officer Group Users",
        query=queries.ilb_user_roles_count,
        model=web.User,
        filter_params={"groups__name": "ILB Case Officer"},
    ),
    CheckQuery(
        name="Home Office Case Officer Group Users",
        query=queries.home_office_user_roles_count,
        model=web.User,
        filter_params={"groups__name": "Home Office Case Officer"},
    ),
    CheckQuery(
        name="NCA Case Officer Group Users",
        query=queries.nca_user_roles_count,
        model=web.User,
        filter_params={"groups__name": "NCA Case Officer"},
    ),
    CheckQuery(
        name="Importer User Group Users",
        query=queries.importer_user_roles_count,
        model=web.User,
        filter_params={"groups__name": "Importer User"},
    ),
    CheckQuery(
        name="Exporter User Group Users",
        query=queries.exporter_user_roles_count,
        model=web.User,
        filter_params={"groups__name": "Exporter User"},
    ),
    CheckQuery(
        name="Constabulary Contacts",
        query=queries.constabulary_user_roles_count,
        model=web.User,
        filter_params={"groups__name": "Constabulary Contact"},
    ),
    CheckQuery(
        name="Import Search Users",
        query=queries.import_search_user_roles_count,
        model=web.User,
        filter_params={"groups__name": "Import Search User"},
    ),
    CheckQuery(
        name="Users With No Group",
        query=queries.users_without_roles_count,
        model=web.User,
        filter_params={"groups__isnull": True},
        exclude_params={"username__endswith": "cancelled"},
        adjustment=24,
        note="",
    ),
    CheckQuery(
        name="User Email Addresses",
        query=queries.email_address_count,
        model=web.Email,
    ),
    CheckQuery(
        name="Import Application Case Notes",
        query=queries.import_application_case_notes_count,
        model=web.ImportApplication.case_notes.through,
    ),
    CheckQuery(
        name="Export Application Case Notes",
        query=queries.export_application_case_notes_count,
        model=web.ExportApplication.case_notes.through,
    ),
    CheckQuery(
        name="Import Application Withdrawals",
        query=queries.withdrawal_import_application_count,
        model=web.WithdrawApplication,
        filter_params={"import_application__isnull": False},
    ),
    CheckQuery(
        name="Export Application Withdrawals",
        query=queries.withdrawal_export_application_count,
        model=web.WithdrawApplication,
        filter_params={"export_application__isnull": False},
    ),
    CheckQuery(
        name="CFS Application Templates",
        query=queries.cat_count,
        model=web.CertificateOfFreeSaleApplicationTemplate,
        bind_vars={"APP_TYPE": "CFS"},
    ),
    CheckQuery(
        name="CFS Application Template Countries",
        query=queries.cat_countries_count,
        model=web.CertificateOfManufactureApplicationTemplate.countries.through,
        bind_vars={"APP_TYPE": "CFS"},
    ),
    CheckQuery(
        name="COM Application Templates",
        query=queries.cat_count,
        model=web.CertificateOfManufactureApplicationTemplate,
        bind_vars={"APP_TYPE": "COM"},
    ),
    CheckQuery(
        name="COM Application Template Countries",
        query=queries.cat_countries_count,
        model=web.CertificateOfManufactureApplicationTemplate.countries.through,
        bind_vars={"APP_TYPE": "COM"},
    ),
    CheckQuery(
        name="GMP Application Templates",
        query=queries.cat_count,
        model=web.CertificateOfGoodManufacturingPracticeApplicationTemplate,
        bind_vars={"APP_TYPE": "GMP"},
    ),
    CheckQuery(
        name="Export Certificates - DRAFT",
        query=queries.export_certificate_draft_count,
        model=web.ExportApplicationCertificate,
        filter_params={"status": "DR"},
    ),
    CheckQuery(
        name="Export Certificates - REVOKED",
        query=queries.export_certificate_revoked_count,
        model=web.ExportApplicationCertificate,
        filter_params={"status": "RE"},
    ),
    CheckQuery(
        name="Export Certificates - ACTIVE",
        query=queries.export_certificate_active_count,
        model=web.ExportApplicationCertificate,
        filter_params={"status": "AC"},
    ),
]

UNIQUE_REFERENCES = [
    CheckQuery(
        name="Import Licence Max Reference",
        model=web.UniqueReference,
        query=queries.ia_licence_max_ref,
        filter_params={"prefix": "ILD"},
        bind_vars={},
    ),
    CheckQuery(
        name="GMP Certificate Max Reference",
        model=web.UniqueReference,
        query=queries.export_certificate_doc_max_ref,
        filter_params={"prefix": "GMP"},
        bind_vars={"like_match": "GMP/2024/%"},
    ),
    CheckQuery(
        name="COM Certificate Max Reference",
        model=web.UniqueReference,
        query=queries.export_certificate_doc_max_ref,
        filter_params={"prefix": "COM"},
        bind_vars={"like_match": "COM/2024/%"},
    ),
    CheckQuery(
        name="CFS Certificate Max Reference",
        model=web.UniqueReference,
        query=queries.export_certificate_doc_max_ref,
        filter_params={"prefix": "CFS"},
        bind_vars={"like_match": "CFS/2024/%"},
    ),
]


FILE_QUERY_DICT = {}

for query_model in files.file_query_model:
    FILE_QUERY_DICT[query_model.query_name] = query_model


CHECK_FILE_COUNTS: list[CheckFileQuery] = [
    CheckFileQuery(
        name="SPS Application Files",
        query_model=FILE_QUERY_DICT["SPS Application Files"],
        model=[
            web.PriorSurveillanceApplication.supporting_documents.through,
            web.PriorSurveillanceContractFile,
        ],
    ),
    CheckFileQuery(
        name="FA-DFL Application Files",
        query_model=FILE_QUERY_DICT["FA-DFL Application Files"],
        model=web.DFLApplication.goods_certificates.through,
    ),
    CheckFileQuery(
        name="FA-OIL Application Files",
        query_model=FILE_QUERY_DICT["FA-OIL Application Files"],
        model=web.UserImportCertificate,
        filter_params={"oil_application__isnull": False},
    ),
    CheckFileQuery(
        name="FA-SIL Application Files",
        query_model=FILE_QUERY_DICT["FA-SIL Application Files"],
        model=[web.UserImportCertificate, web.SILUserSection5],
        filter_params={"sil_application__isnull": False},
    ),
    CheckFileQuery(
        name="Sanctions & Adhoc Application Files",
        query_model=FILE_QUERY_DICT["Sanctions & Adhoc Application Files"],
        model=web.SanctionsAndAdhocApplication.supporting_documents.through,
    ),
    CheckFileQuery(
        name="OPT Application Files",
        query_model=FILE_QUERY_DICT["OPT Application Files"],
        model=web.OutwardProcessingTradeApplication.documents.through,
    ),
    CheckFileQuery(
        name="Wood Application Files",
        query_model=FILE_QUERY_DICT["Wood Application Files"],
        model=web.WoodQuotaApplication.supporting_documents.through,
        adjustment=2,
    ),
    CheckFileQuery(
        name="Textiles Application Files",
        query_model=FILE_QUERY_DICT["Textiles Application Files"],
        model=web.TextilesApplication.supporting_documents.through,
    ),
    CheckFileQuery(
        name="Firearms & Ammunition Certificate Files",
        query_model=FILE_QUERY_DICT["Firearms & Ammunition Certificate Files"],
        model=[
            web.SILSupplementaryReportFirearmSection1,
            web.SILSupplementaryReportFirearmSection2,
            web.SILSupplementaryReportFirearmSection5,
            web.SILSupplementaryReportFirearmSection582Obsolete,  # /PS-IGNORE
            web.SILSupplementaryReportFirearmSection582Other,  # /PS-IGNORE
        ],
    ),
    CheckFileQuery(
        name="Further Information Request Files",
        query_model=FILE_QUERY_DICT["Further Information Request Files"],
        model=web.FurtherInformationRequest.files.through,
    ),
    CheckFileQuery(
        name="Mailshot Files",
        query_model=FILE_QUERY_DICT["Mailshot Files"],
        model=web.Mailshot.documents.through,
    ),
    CheckFileQuery(
        name="GMP Application Files",
        query_model=FILE_QUERY_DICT["GMP Application Files"],
        model=web.GMPFile,
    ),
    CheckFileQuery(
        name="Import Application Case Note Files",
        query_model=FILE_QUERY_DICT["Import Application Case Note Files"],
        model=web.CaseNote,
        filter_params={"importapplication__isnull": False, "files__isnull": False},
    ),
    CheckFileQuery(
        name="Export Application Case Note Documents",
        query_model=FILE_QUERY_DICT["Export Application Case Note Documents"],
        model=web.CaseNote,
        filter_params={"exportapplication__isnull": False, "files__isnull": False},
        path_prefixes=["export_case_note_docs"],
    ),
    CheckFileQuery(
        name="Supplementary Report Goods Uploaded Files",
        query_model=FILE_QUERY_DICT["Supplementary Report Goods Uploaded Files"],
        model=web.DFLSupplementaryReportFirearm,
        filter_params={"is_upload": True},
        path_prefixes=["fa_supplementary_report_upload_files"],
    ),
    CheckFileQuery(
        name="Import Application Licence Documents",
        query_model=FILE_QUERY_DICT["Import Application Licence Documents"],
        model=web.CaseDocumentReference,
        filter_params={
            "document_type__in": [
                "LICENCE",
                "COVER_LETTER",
            ]
        },
        path_prefixes=["import_licence_docs", "import_cover_letter"],
    ),
    CheckFileQuery(
        name="Export Application Certificate Documents",
        query_model=FILE_QUERY_DICT["Export Application Certificate Documents"],
        model=web.CaseDocumentReference,
        filter_params={"document_type": web.CaseDocumentReference.Type.CERTIFICATE},
        path_prefixes=["export_certificate"],
    ),
]
