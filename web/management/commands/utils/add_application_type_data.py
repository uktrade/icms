from web.models import ExportApplicationType, ImportApplicationType, Template


def add_export_application_type_data():
    ExportApplicationType.objects.create(
        type_code="CFS",
        type="Certificate of Free Sale",
        allow_multiple_products=True,
        generate_cover_letter=False,
        allow_hse_authorization=False,
    )

    ExportApplicationType.objects.create(
        type_code="COM",
        type="Certificate of Manufacture",
        allow_multiple_products=False,
        generate_cover_letter=False,
        allow_hse_authorization=False,
    )

    ExportApplicationType.objects.create(
        type_code="GMP",
        type="Certificate of Good Manufacturing Practice",
        allow_multiple_products=False,
        generate_cover_letter=False,
        allow_hse_authorization=False,
    )


def add_import_application_type_data():
    gen_dec = Template.objects.get(template_code=Template.Codes.IMA_GEN_DECLARATION)
    opt_dec = Template.objects.get(template_code=Template.Codes.IMA_OPT_DECLARATION)
    sps_dec = Template.objects.get(template_code=Template.Codes.IMA_SPS_DECLARATION)
    wd_dec = Template.objects.get(template_code=Template.Codes.IMA_WD_DECLARATION)

    #
    # Active application types
    #
    ImportApplicationType.objects.create(
        is_active=True,
        type="FA",
        sub_type="OIL",
        name="Firearms and Ammunition (Open Individual Import Licence)",
        licence_type_code="FIREARMS",
        sigl_flag=False,
        chief_flag=True,
        chief_licence_prefix="GBOIL",
        paper_licence_flag=False,
        electronic_licence_flag=True,
        cover_letter_flag=True,
        cover_letter_schedule_flag=False,
        category_flag=True,
        default_licence_length_months=36,
        default_commodity_desc="Firearms, component parts thereof, or ammunition of any applicable commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended.",
        quantity_unlimited_flag=True,
        exp_cert_upload_flag=False,
        supporting_docs_upload_flag=False,
        multiple_commodities_flag=False,
        guidance_file_url="/docs/ApplyingForFirearmsOILLicence.pdf",
        usage_auto_category_desc_flag=False,
        case_checklist_flag=True,
        importer_printable=False,
        declaration_template=gen_dec,
    )

    ImportApplicationType.objects.create(
        is_active=True,
        type="FA",
        sub_type="DEACTIVATED",
        name="Firearms and Ammunition (Deactivated Firearms Licence)",
        licence_type_code="FIREARMS",
        sigl_flag=False,
        chief_flag=True,
        chief_licence_prefix="GBSIL",
        paper_licence_flag=True,
        electronic_licence_flag=True,
        cover_letter_flag=True,
        cover_letter_schedule_flag=True,
        category_flag=True,
        default_licence_length_months=6,
        quantity_unlimited_flag=True,
        exp_cert_upload_flag=False,
        supporting_docs_upload_flag=False,
        multiple_commodities_flag=True,
        guidance_file_url="/docs/ApplyingForFirearmsSILLicence.pdf",
        usage_auto_category_desc_flag=False,
        case_checklist_flag=True,
        importer_printable=False,
        declaration_template=gen_dec,
    )

    ImportApplicationType.objects.create(
        is_active=True,
        type="FA",
        sub_type="SIL",
        name="Firearms and Ammunition (Specific Individual Import Licence)",
        licence_type_code="FIREARMS",
        sigl_flag=False,
        chief_flag=True,
        chief_licence_prefix="GBSIL",
        paper_licence_flag=True,
        electronic_licence_flag=True,
        cover_letter_flag=True,
        cover_letter_schedule_flag=True,
        category_flag=True,
        default_licence_length_months=6,
        quantity_unlimited_flag=False,
        exp_cert_upload_flag=False,
        supporting_docs_upload_flag=False,
        multiple_commodities_flag=True,
        guidance_file_url="/docs/ApplyingForFirearmsSILLicence.pdf",
        usage_auto_category_desc_flag=False,
        case_checklist_flag=True,
        importer_printable=False,
        declaration_template=gen_dec,
    )

    ImportApplicationType.objects.create(
        is_active=True,
        type="ADHOC",
        sub_type="ADHOC1",
        name="Sanctions and Adhoc Licence Application",
        licence_type_code="ADHOC",
        sigl_flag=False,
        chief_flag=True,
        chief_licence_prefix="GBSAN",
        paper_licence_flag=False,
        electronic_licence_flag=True,
        cover_letter_flag=False,
        cover_letter_schedule_flag=False,
        category_flag=True,
        quantity_unlimited_flag=False,
        unit_list_csv="KGS,BARRELS",
        exp_cert_upload_flag=False,
        supporting_docs_upload_flag=True,
        multiple_commodities_flag=True,
        guidance_file_url="/docs/ApplyingForSanctionsLicence.pdf",
        usage_auto_category_desc_flag=False,
        case_checklist_flag=True,
        importer_printable=False,
        declaration_template=gen_dec,
    )

    ImportApplicationType.objects.create(
        is_active=True,
        type="WD",
        sub_type="QUOTA",
        name="Wood (Quota)",
        licence_type_code="WOOD",
        sigl_flag=False,
        chief_flag=False,
        paper_licence_flag=True,
        electronic_licence_flag=False,
        cover_letter_flag=False,
        cover_letter_schedule_flag=False,
        category_flag=False,
        default_licence_length_months=12,
        quantity_unlimited_flag=False,
        unit_list_csv="M3",
        exp_cert_upload_flag=False,
        supporting_docs_upload_flag=True,
        multiple_commodities_flag=False,
        guidance_file_url="/docs/ApplyingForWoodLicence.pdf",
        usage_auto_category_desc_flag=False,
        case_checklist_flag=True,
        importer_printable=False,
        declaration_template=wd_dec,
    )

    #
    # Inactive application types
    #

    ImportApplicationType.objects.create(
        is_active=False,
        type="OPT",
        sub_type="QUOTA",
        name="Outward Processing Trade",
        licence_type_code="OPT",
        sigl_flag=True,
        chief_flag=False,
        paper_licence_flag=True,
        electronic_licence_flag=False,
        cover_letter_flag=False,
        cover_letter_schedule_flag=False,
        category_flag=True,
        sigl_category_prefix="ZA,ZTA",
        default_licence_length_months=9,
        quantity_unlimited_flag=False,
        unit_list_csv="KGS",
        exp_cert_upload_flag=False,
        supporting_docs_upload_flag=True,
        multiple_commodities_flag=False,
        guidance_file_url="/docs/ApplyingForOPTLicence.pdf",
        usage_auto_category_desc_flag=False,
        case_checklist_flag=True,
        importer_printable=False,
        declaration_template=opt_dec,
    )

    ImportApplicationType.objects.create(
        is_active=False,
        type="TEX",
        sub_type="QUOTA",
        name="Textiles (Quota)",
        licence_type_code="QUOTA",
        sigl_flag=True,
        chief_flag=True,
        chief_licence_prefix="GBTEX",
        paper_licence_flag=True,
        electronic_licence_flag=True,
        cover_letter_flag=False,
        cover_letter_schedule_flag=False,
        category_flag=True,
        sigl_category_prefix="A",
        default_licence_length_months=6,
        quantity_unlimited_flag=False,
        exp_cert_upload_flag=False,
        supporting_docs_upload_flag=True,
        multiple_commodities_flag=False,
        guidance_file_url="/docs/ApplyingForTextilesLicence.pdf",
        licence_category_description="Goods of the commodity code in Box 10 or any other commodity code under the category valid at the time of issue.",
        usage_auto_category_desc_flag=False,
        case_checklist_flag=True,
        importer_printable=False,
        declaration_template=gen_dec,
    )

    ImportApplicationType.objects.create(
        is_active=False,
        type="SPS",
        sub_type="SPS1",
        name="Prior Surveillance",
        licence_type_code="SURVEILLANCE",
        sigl_flag=True,
        chief_flag=True,
        chief_licence_prefix="GBAOG",
        paper_licence_flag=True,
        electronic_licence_flag=True,
        cover_letter_flag=False,
        cover_letter_schedule_flag=False,
        category_flag=False,
        default_licence_length_months=4,
        quantity_unlimited_flag=False,
        unit_list_csv="KGS",
        exp_cert_upload_flag=False,
        supporting_docs_upload_flag=True,
        multiple_commodities_flag=False,
        guidance_file_url="/docs/DoINeedAnImportLicence.pdf",
        usage_auto_category_desc_flag=True,
        case_checklist_flag=False,
        importer_printable=True,
        declaration_template=sps_dec,
    )


def add_import_application_type_endorsements():
    # OIL
    iat = ImportApplicationType.objects.get(sub_type=ImportApplicationType.SubTypes.OIL)
    endorsement = Template.objects.get(pk=21)
    iat.endorsements.add(endorsement)

    # SIL
    iat = ImportApplicationType.objects.get(sub_type=ImportApplicationType.SubTypes.SIL)
    endorsement = Template.objects.get(pk=57)
    iat.endorsements.add(endorsement)

    # DFL
    iat = ImportApplicationType.objects.get(sub_type=ImportApplicationType.SubTypes.DFL)
    iat.endorsements.add(endorsement)
