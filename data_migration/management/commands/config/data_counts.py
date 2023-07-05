from django.db.models import Count

import web.models as web
from data_migration.management.commands._types import CheckCount, CheckQuery
from data_migration.models import queries
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
        name="Users With Multiple Groups",
        expected_count=0,
        model=web.User,
        filter_params={"group_count__gt": 1},
        annotation={"group_count": Count("groups")},
    ),
]

CHECK_DATA_QUERIES: list[CheckQuery] = [
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
    ),
    CheckQuery(
        name="Template Coutries",
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
        name="Users With No Group",
        query=queries.users_without_roles_count,
        model=web.User,
        filter_params={"groups__isnull": True},
    ),
]
