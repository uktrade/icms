import datetime as dt

from data_migration import queries

from . import xml_data as xd

IA_BASE_COLUMNS = [
    ("ima_id",),
    ("imad_id",),
    ("file_folder_id",),
    ("reference",),
    ("status",),
    ("submit_datetime",),
    ("create_datetime",),
    ("created",),
    ("variation_no",),
    ("submitted_by_id",),
    ("created_by_id",),
    ("last_updated_by_id",),
    ("importer_id",),
    ("importer_office_legacy_id",),
    ("contact_id",),
    ("application_type_id",),
    ("process_type",),
    ("decision",),
    ("variations_xml",),
    ("last_update_datetime",),
]

ia_query_result = {
    queries.section5_clauses: (
        [
            ("clause",),
            ("legacy_code",),
            ("description",),
            ("is_active",),
            ("created_datetime",),
            ("created_by_id",),
            ("updated_datetime",),
            ("updated_by_id",),
        ],
        [
            (
                "A",
                "A",
                "Aa",
                1,
                dt.datetime(2020, 6, 29, 7),
                2,
                None,
                None,
            ),
            (
                "B",
                "B",
                "Bb",
                1,
                dt.datetime(2021, 5, 28, 7),
                2,
                None,
                None,
            ),
            (
                "Test Clause",
                "5_1_ABA",
                "Test Description",
                1,
                dt.datetime.now(),
                2,
                dt.datetime.now(),
                2,
            ),
        ],
    ),
    queries.textiles_checklist: (
        [
            ("imad_id",),
            ("case_update",),
            ("fir_required",),
            ("response_preparation",),
            ("validity_period_correct",),
            ("endorsements_listed",),
            ("authorisation",),
            ("within_maximum_amount_limit",),
        ],
        [
            (51, "N", "N/A", "true", "Y", "Y", "true", "true"),
            (52, "Y", "N", "true", "Y", "Y", None, "false"),
            (53, None, None, None, None, None, None, None),
        ],
    ),
    queries.oil_checklist: (
        [
            ("imad_id",),
            ("case_update",),
            ("fir_required",),
            ("response_preparation",),
            ("validity_period_correct",),
            ("endorsements_listed",),
            ("authorisation",),
            ("within_maximum_amount_limit",),
            ("authority_required",),
            ("authority_received",),
            ("authority_police",),
        ],
        [
            (31, "N", "N/A", "true", "Y", "Y", "true", "true", "Y", "Y", "NA"),
            (32, "Y", "N", "true", "Y", "Y", None, "false", "N", "N", "N"),
        ],
    ),
    queries.sil_checklist: (
        [
            ("imad_id",),
            ("case_update",),
            ("fir_required",),
            ("response_preparation",),
            ("validity_period_correct",),
            ("endorsements_listed",),
            ("authorisation",),
            ("within_maximum_amount_limit",),
            ("authority_required",),
            ("authority_received",),
            ("authority_police",),
            ("auth_cover_items_listed",),
            ("within_auth_restrictions",),
        ],
        [
            (11, "N", "N/A", "true", "Y", "Y", "true", "true", "Y", "Y", "NA", "Y", "Y"),
            (12, "Y", "N", "true", "Y", "Y", None, "false", "N", "N", "N", "N", "N"),
        ],
    ),
    queries.fa_authorities: (
        [
            ("id",),
            ("is_active",),
            ("reference",),
            ("certificate_type",),
            ("address",),
            ("postcode",),
            ("importer_id",),
            ("file_folder_id",),
            ("archive_reason",),
            ("other_archive_reason",),
        ],
        [
            (1, 1, "A", "RFD", "123 Test", "LN1", 2, 102, None, None),
            (2, 1, "B", "SHOTGUN", "234 Test", "LN2", 3, 103, None, None),
            (3, 0, "C", "SHOTGUN", "567 Test", "LN2", 3, 106, "OTHER,WITHDRAWN", "Given Reason"),
        ],
    ),
    queries.section5_authorities: (
        [
            ("id",),
            ("is_active",),
            ("reference",),
            ("address",),
            ("postcode",),
            ("importer_id",),
            ("file_folder_id",),
            ("archive_reason",),
            ("other_archive_reason",),
        ],
        [
            (1, 1, "A", "123 Test", "LN1", 2, 104, None, None),
            (2, 1, "B", "234 Test", "LN2", 3, 105, None, None),
            (3, 0, "C", "567 Test", "LN2", 3, 107, "REFUSED", None),
        ],
    ),
    queries.fa_authority_linked_offices: (
        [("firearmsauthority_id",), ("office_legacy_id",)],
        [(1, "i-2-1"), (1, "i-2-2"), (2, "i-3-1")],
    ),
    queries.section5_linked_offices: (
        [("section5authority_id",), ("office_legacy_id",)],
        [(1, "i-2-1"), (1, "i-2-2"), (2, "i-3-1")],
    ),
    queries.ia_licence: (
        [
            ("ima_id",),
            ("imad_id",),
            ("licence_start_date",),
            ("licence_end_date",),
            ("case_reference",),
            ("issue_paper_licence_only",),
            ("status",),
            ("variation_no",),
            ("created_at",),
            ("updated_at",),
            ("case_completion_datetime",),
            ("document_pack_id",),
            ("revoke_reason",),
            ("revoke_email_sent",),
        ],
        [
            (
                1,  # ima_id
                11,  # imad_id
                dt.date(2022, 4, 27),  # licence_start_date
                dt.date(2023, 4, 27),  # licence_end_date
                "IMA/2022/1234",  # case_reference
                0,  # issue_paper_licence_only
                "AC",  # status
                0,  # variation_number
                dt.datetime(2022, 4, 27, 10, 43),  # created_at
                dt.datetime(2022, 4, 27, 10, 44),  # updated_at
                dt.datetime(2022, 4, 27, 10, 44),  # case_completion_datetime
                1,  # document_pack_id
                None,  # revoke_reason
                0,  # revoke_email_sent
            ),
            (
                2,  # ima_id
                9,  # imad_id
                dt.date(2022, 4, 27),  # licence_start_date
                dt.date(2023, 4, 30),  # licence_end_date
                "IMA/2022/2345",  # case_reference
                1,  # issue_paper_licence_only
                "AR",  # status
                0,  # variation_number
                dt.datetime(2022, 4, 27, 10, 43),  # created_at
                dt.datetime(2022, 4, 27, 10, 44),  # updated_at
                dt.datetime(2022, 4, 27, 10, 44),  # case_completion_datetime
                2,  # document_pack_id
                None,  # revoke_reason
                0,  # revoke_email_sent
            ),
            (
                2,  # ima_id
                10,  # imad_id
                dt.date(2022, 4, 27),  # licence_start_date
                dt.date(2023, 5, 30),  # licence_end_date
                "IMA/2022/2345/1",  # case_reference
                0,  # issue_papaer_licence_only
                "RE",  # status
                1,  # variation_number
                dt.datetime(2022, 4, 27, 10, 43),  # created_at
                dt.datetime(2022, 4, 27, 10, 44),  # updated_at
                dt.datetime(2022, 4, 27, 10, 44),  # case_completion_datetime
                3,  # document_pack_id
                "Test revoke reason",  # revoke_reason
                1,  # revoke_email_sent
            ),
            (
                2,  # ima_id
                12,  # imad_id
                dt.date(2022, 4, 27),  # licence_start_date
                dt.date(2023, 6, 30),  # licence_end_date
                "IMA/2022/2345/2",  # case_reference
                0,  # issue_paper_licence_only
                "AC",  # status
                2,  # variation_number
                dt.datetime(2022, 4, 27, 10, 43),  # created_at
                dt.datetime(2022, 4, 27, 10, 44),  # updated_at
                dt.datetime(2022, 4, 27, 10, 44),  # case_completion_datetime
                4,  # document_pack_id
                None,  # revoke_reason
                0,  # revoke_email_sent
            ),
            (
                3,  # ima_id
                13,  # imad_id
                dt.date(2022, 4, 27),  # licence_start_date
                dt.date(2023, 6, 30),  # licence_end_date
                "IMA/2022/2346",  # case_reference
                0,  # issue_paper_licence_only
                "AC",  # status
                2,  # variation_number
                dt.datetime(2022, 4, 27, 10, 43),  # created_at
                dt.datetime(2022, 4, 27, 10, 44),  # updated_at
                dt.datetime(2022, 4, 27, 10, 44),  # case_completion_datetime
                6,  # document_pack_id
                None,  # revoke_reason
                0,  # revoke_email_sent
            ),
        ],
    ),
    queries.ia_document_pack_acknowledged: (
        [("importapplicationlicence_id",), ("user_id",)],
        [(1, 2), (3, 2), (4, 2), (4, 3)],
    ),
    queries.ia_licence_docs: (
        [
            ("reference",),
            ("licence_id",),
            ("document_legacy_id",),
            ("document_type",),
            ("filename",),
            ("content_type",),
            ("file_size",),
            ("path",),
            ("created_datetime",),
            ("created_by_id",),
            ("signed_datetime",),
            ("signed_by_id",),
        ],
        [
            (
                "1234A",  # reference
                11,  # licence_id
                1,  # document_legacy_id
                "LICENCE",  # document_type
                "Firearms Licence",  # filename
                "application/pdf",  # content_type
                100,  # file_size
                "firearms-licence-1.pdf",  # path
                dt.datetime(2022, 4, 27, 7),  # created_datetime
                2,  # created_by_id
                dt.datetime(2022, 4, 27, 7),  # signed_datetime
                2,  # signed_by_id
            ),
            (
                None,  # reference
                11,  # licence_id
                6,  # document_legacy_id
                "COVER_LETTER",  # document_type
                "Firearms Cover",  # filename
                "application/pdf",  # content_type
                100,  # file_size
                "firearms-cover-1.pdf",  # path
                dt.datetime(2022, 4, 27, 7),  # created_datetime
                2,  # created_by_id
                dt.datetime(2022, 4, 27, 7),  # signed_datetime
                2,  # signed_by_id
            ),
            (
                "1235B",  # reference
                9,  # licence_id
                2,  # document_legacy_id
                "LICENCE",  # document_type
                "Firearms Licence",  # filename
                "application/pdf",  # content_type
                100,  # file_size
                "firearms-licence-2.pdf",  # path
                dt.datetime(2022, 4, 27, 7),  # created_datetime
                2,  # created_by_id
                dt.datetime(2022, 4, 27, 7),  # signed_datetime
                2,  # signed_by_id
            ),
            (
                "1236C",  # referece
                10,  # licence_id
                3,  # document_legacy_id
                "LICENCE",  # document_type
                "Firearms Licence",  # filename
                "application/pdf",  # content_type
                100,  # file_size
                "firearms-licence-3.pdf",  # path
                dt.datetime(2022, 4, 27, 7),  # created_datetime
                2,  # created_by_id
                dt.datetime(2022, 4, 27, 7),  # signed_datetime
                2,  # signed_by_id
            ),
            (
                "1237E",  # referece
                12,  # licence_id
                5,  # document_legacy_id
                "LICENCE",  # filename
                "Firearms Licence",  # content_type
                "application/pdf",  # content_type
                100,  # path
                "firearms-licence-5.pdf",  # path
                dt.datetime(2022, 4, 30, 7),  # created_datetime
                2,  # created_by_id
                dt.datetime(2022, 4, 30, 7),  # signed_datetime
                2,  # signed_by_id
            ),
            (
                None,  # reference
                12,  # licence_id
                7,  # document_legacy_id
                "COVER_LETTER",  # document_type
                "Firearms Cover",  # filename
                "application/pdf",  # content_type
                100,  # file_size
                "firearms-cover-2.pdf",  # path
                dt.datetime(2022, 4, 27, 7),  # created_datetime
                2,  # created_by_id
                dt.datetime(2022, 4, 27, 7),  # signed_datetime
                2,  # signed_by_id
                "COVER",  # prefix
            ),
        ],
    ),
    queries.ia_legacy_licence_references: (
        [("licence_id",), ("reference",), ("document_type",)],
        [(13, "123456L", "LICENCE")],
    ),
    queries.ia_licence_doc_refs: (
        [("prefix",), ("reference_no",), ("uref",)],
        [
            ("ILD", "1234", "ILD1234"),
            ("ILD", "1235", "ILD1235"),
            ("ILD", "12346", "ILD12346"),
            ("ILD", "1237", "ILD1237"),
            ("ILD", "0001110", "ILD0001110"),
            ("ILD", "0001111", "ILD0001111"),
            ("ILD", "123456", "ILD123456"),
        ],
    ),
    queries.opt_application: (
        IA_BASE_COLUMNS
        + [
            ("customs_office_name",),
            ("customs_office_address",),
            ("rate_of_yield",),
            ("rate_of_yield_calc_method",),
            ("last_export_day",),
            ("reimport_period",),
            ("nature_process_ops",),
            ("suggested_id",),
            ("cp_origin_country_id",),
            ("cp_processing_country_id",),
            ("commodity_group_id",),
            ("cp_total_quantity",),
            ("cp_total_value",),
            ("cp_commodities_xml",),
            ("teg_origin_country_id",),
            ("teg_total_quantity",),
            ("teg_total_value",),
            ("teg_goods_description",),
            ("teg_commodities_xml",),
            ("fq_similar_to_own_factory",),
            ("fq_manufacturing_within_eu",),
            ("fq_maintained_in_eu",),
            ("fq_maintained_in_eu_r",),
            ("fq_employment_decreased",),
            ("fq_employment_decreased_r",),
            ("fq_prior_authorisation",),
            ("fq_prior_authorisation_r",),
            ("fq_past_beneficiary",),
            ("fq_past_beneficiary_r",),
            ("fq_new_application",),
            ("fq_new_application_reasons",),
            ("fq_further_authorisation",),
            ("fq_further_auth_reasons",),
            ("fq_subcontract_production",),
        ],
        [
            (
                11,  # ima_id
                21,  # imad_id
                10,  # file_folder_id
                "IMA/2022/2234",  # reference
                "COMPLETED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8),  # create_datetime
                dt.datetime(2022, 4, 22, 8),  # created
                0,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                3,  # application_type
                "OutwardProcessingTradeApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
                "Test",  # customs_office_name
                "Test Address",  # customs_office_address
                0.5,  # rate_of_yield
                "abc",  # rate_of_yield_calc_method
                dt.date(2023, 4, 23),  # last_export_day
                12,  # reimport_period
                "test",  # nature_process_ops
                "test",  # suggested_id
                1,  # cp_origin_country_id
                1,  # cp_processing_country_id
                1,  # commodity_group_id
                123,  # cp_total_quantity
                100,  # cp_total_value
                xd.opt_commodities,  # cp_commodities_xml
                1,  # teg_origin_country_id
                100,  # teg_total_quantity
                500,  # teg_total_value
                "test",  # teg_goods_description
                xd.opt_commodities,  # teg_commodities_xml
                "Y",  # fq_similar_to_own_factory
                "Y",  # fq_manufacturing_within_eu
                "Y",  # fq_maintained_in_eu
                "test eu",  # fq_maintained_in_eu_r
                "N",  # fq_employment_decreased
                "test em",  # fq_employment_decreased_r
                "Y",  # fq_prior_authorisation
                "test pa",  # fq_prior_authorisation_r
                "Y",  # fq_past_beneficiary
                "test pb",  # fq_past_beneficiary_r
                "Y",  # fq_new_application
                "test na",  # fq_new_application_reasons
                "Y",  # fq_further_authorisation
                "test fa",  # fq_further_auth_reasons
                "Y",  # fq_subcontract_production
            ),
            (
                12,  # ima_id
                22,  # imad_id
                11,  # file_folder_id
                "IMA/2022/2235",  # reference
                "COMPLETED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8),  # create_datetime
                dt.datetime(2022, 4, 22, 8),  # created
                0,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                3,  # application_type
                "OutwardProcessingTradeApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
                "Test",  # customs_office_name
                "Test Address",  # customs_office_address
                0.5,  # rate_of_yield
                "abc",  # rate_of_yield_calc_method
                dt.date(2023, 4, 23),  # last_export_day
                12,  # reimport_period
                "test",  # nature_process_ops
                "test",  # suggested_id
                1,  # cp_origin_country_id
                1,  # cp_processing_country_id
                1,  # commodity_group_id
                None,  # cp_total_quantity
                None,  # cp_total_value
                None,  # cp_commodities_xml
                1,  # teg_origin_country_id
                None,  # teg_total_quantity
                None,  # teg_total_value
                None,  # teg_goods_description
                None,  # teg_commodities_xml
                "N",  # fq_similar_to_own_factory
                "N",  # fq_manufacturing_within_eu
                "N",  # fq_maintained_in_eu
                None,  # fq_maintained_in_eu_r
                "N",  # fq_employment_decreased
                None,  # fq_employment_decreased_r
                "N",  # fq_prior_authorisation
                None,  # fq_prior_authorisation_r
                "N",  # fq_past_beneficiary
                None,  # fq_past_beneficiary_r
                "N",  # fq_new_application
                None,  # fq_new_application_reasons
                "N",  # fq_further_authorisation
                None,  # fq_further_auth_reasons
                "N",  # fq_subcontract_production
            ),
        ],
    ),
    queries.sanctions_application: (
        IA_BASE_COLUMNS
        + [
            ("exporter_name",),
            ("exporter_address",),
            ("commodities_xml",),
            ("commodities_response_xml",),
            ("sanction_emails_xml",),
        ],
        [
            (
                60,  # ima_id
                70,  # imad_id
                60,  # file_folder_id
                "IMA/2022/6234",  # reference
                "COMPLETED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8),  # create_datetime
                dt.datetime(2022, 4, 22, 8),  # created
                0,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                12,  # application_type
                "SanctionsApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
                "Test Exporter",  # exporter_name
                "123 Somewhere",  # exporter_address
                xd.sanctions_commodities,  # commodities_xml
                xd.sanctions_commodities_response,  # commodities_response_xml
                xd.sanctions_emails,  # sanction_emails_xml
            )
        ],
    ),
    queries.sps_application: (
        IA_BASE_COLUMNS
        + [
            ("quantity",),
            ("value_gbp",),
            ("value_eur",),
            ("file_type",),
            ("target_id",),
            ("commodity_id",),
            ("licence_uref_id",),
            ("customs_cleared_to_uk",),
            ("chief_usage_status",),
        ],
        [
            (
                100,  # ima_id
                1110,  # imad_id
                100,  # file_folder_id
                "IMA/2022/10234",  # reference
                "COMPLETED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8),  # create_datetime
                dt.datetime(2022, 4, 22, 8),  # created
                0,  # variation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "PriorSurveillanceApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
                "NONSENSE",  # quantity
                "NONSENSE",  # value_gbp
                "NONSENSE",  # value_eur
                "PRO_FORMA_INVOICE",  # file_type
                1000,  # target_id
                1,  # commodity_id
                "ILD0001110",  # licence_uref_id
                True,  # customs_cleared_to_uk
                "D",  # chief usage status
            ),
            (
                101,  # ima_id
                1111,  # imad_id
                101,  # file_folder_id
                "IMA/2022/10235",  # reference
                "COMPLETED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8),  # create_datetime
                dt.datetime(2022, 4, 22, 8),  # created
                0,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "PriorSurveillanceApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
                100,  # quantity
                100,  # value_gbp
                100,  # value_eur
                "SUPPLY_CONTRACT",  # file_type
                1001,  # target_id
                2,  # commodity_id
                "ILD0001111",  # licence_uref_id
                False,  # customs_cleared_to_uk
                "E",  # chief usage status
            ),
        ],
    ),
    queries.textiles_application: (
        IA_BASE_COLUMNS,
        [
            (
                41,  # ima_id
                51,  # imad_id
                41,  # file_folder_id
                "IMA/2022/4234",  # reference
                "COMPLETED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8),  # create_datetime
                dt.datetime(2022, 4, 22, 8),  # created
                0,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "TexilesQuotaApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
            ),
            (
                42,  # ima_id
                52,  # imad_id
                42,  # file_folder_id
                "IMA/2022/4235",  # reference
                "COMPLETED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8),  # create_datetime
                dt.datetime(2022, 4, 22, 8),  # created
                0,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "TexilesQuotaApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
            ),
            (
                43,  # ima_id
                53,  # imad_id
                43,  # file_folder_id
                "IMA/2022/4236",  # reference
                "COMPLETED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8),  # create_datetime
                dt.datetime(2022, 4, 22, 8),  # created
                0,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "TexilesQuotaApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
            ),
        ],
    ),
    queries.dfl_application: (
        IA_BASE_COLUMNS
        + [
            ("deactivated_firearm",),
            ("proof_checked",),
            ("constabulary_id",),
            ("supplementary_report_xml",),
            ("fa_goods_certs_xml",),
            ("commodities_response_xml",),
            ("cover_letter_text",),
            ("withdrawal_xml",),
        ],
        [
            (
                51,  # ima_id
                61,  # imad_id
                51,  # file_folder_id
                "IMA/2022/5234",  # reference
                "COMPLETED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8),  # create_datetime
                dt.datetime(2022, 4, 22, 8),  # created
                0,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                10,  # application_type
                "DFLApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
                True,  # deactivated_firearm
                True,  # proof_checked
                1,  # constabulary_id
                xd.dfl_sr,  # supplementary_report_xml
                xd.dfl_goods_cert,  # fa_goods_cert_xml
                xd.dfl_goods_response,  # commodities_response_xml
                xd.cover_letter_text_dfl_v1,  # cover_letter_text
                None,  # withdrawal_xml
            ),
            (
                52,  # ima_id
                62,  # imad_id
                52,  # file_folder_id
                "IMA/2022/5235",  # reference
                "REVOKED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8),  # create_datetime
                dt.datetime(2022, 4, 22, 8),  # created
                0,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                10,  # application_type
                "DFLApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
                True,  # deactivated_firearm
                True,  # proof_checked
                1,  # constabulary_id
                None,  # supplementary_report_xml
                None,  # fa_goods_cert_xml
                None,  # commodities_response_xml
                None,  # cover_letter_text
                None,  # withdrawal_xml
            ),
            (
                53,  # ima_id
                63,  # imad_id
                53,  # file_folder_id
                "IMA/2022/5236",  # reference
                "WITHDRAWN",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8),  # create_datetime
                dt.datetime(2022, 4, 22, 8),  # created
                0,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                10,  # application_type
                "DFLApplication",  # process_type
                None,  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
                True,  # deactivated_firearm
                True,  # proof_checked
                1,  # constabulary_id
                None,  # supplementary_report_xml
                None,  # fa_goods_cert_xml
                None,  # commodities_response_xml
                None,  # cover_letter_text
                xd.import_withdrawal,  # withdrawal_xml
            ),
        ],
    ),
    queries.oil_application: (
        IA_BASE_COLUMNS
        + [
            ("section1",),
            ("section2",),
            ("bought_from_details_xml",),
            ("supplementary_report_xml",),
        ],
        [
            (
                21,  # ima_id
                31,  # imad_id
                21,  # file_folder_id
                "IMA/2022/3234",  # reference
                "COMPLETED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8),  # create_datetime
                dt.datetime(2022, 4, 22, 8),  # created
                0,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                5,  # application_type
                "OpenIndividualLicenceApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
                1,  # section1
                1,  # section2
                None,  # bought_from_details_xml
                xd.sr_upload_xml,  # supplementary_report_xml
            ),
            (
                22,  # ima_id
                32,  # imad_id
                22,  # file_folder_id
                "IMA/2022/3235",  # reference
                "COMPLETED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8),  # create_datetime
                dt.datetime(2022, 4, 22, 8),  # created
                0,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                5,  # application_type
                "OpenIndividualLicenceApplication",  # process_type
                "REFUSE",  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
                1,  # section1
                0,  # section2
                xd.import_contact_xml,  # bought_from_details_xml
                xd.sr_manual_xml,  # supplementary_report_xml
            ),
        ],
    ),
    queries.sil_application: (
        IA_BASE_COLUMNS
        + [
            ("section1",),
            ("section2",),
            ("section5",),
            ("section58_obsolete",),
            ("section58_other",),
            ("bought_from_details_xml",),
            ("supplementary_report_xml",),
            ("commodities_xml",),
            ("commodities_response_xml",),
            ("licence_uref_id",),
        ],
        [
            (
                1,  # ima_id
                11,  # imad_id
                1,  # file_folder_id
                "IMA/2022/1234",  # reference
                "PROCESSING",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 9, 23, 22),  # create_datetime
                dt.datetime(2022, 4, 22, 9, 23, 22),  # created
                0,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                6,  # application_type
                "SILApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
                1,  # section1
                1,  # section2
                1,  # section5
                1,  # section58_obsolete
                1,  # section58_other
                None,  # bought_from_details_xml
                xd.sr_manual_xml_5_goods,  # supplementary_report_xml
                xd.sil_goods,  # commodities_xml
                xd.sil_response_goods,  # commodities_response_xml
                "ILD1234",  # licence_uref
            ),
            (
                2,  # ima_id
                12,  # imad_id
                2,  # file_folder_id
                "IMA/2022/2345",  # reference
                "COMPLETED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 8, 44, 44),  # create_datetime
                dt.datetime(2022, 4, 22, 8, 44, 44),  # created
                2,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                None,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                6,  # application_type
                "SILApplication",  # process_type
                "APPROVE",  # decision
                xd.open_variation,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
                1,  # section1
                1,  # section2
                1,  # section5
                1,  # section58_obsolete
                1,  # section58_other
                xd.import_contact_xml,  # bought_from_details_xml
                xd.sr_upload_xml,  # supplementary_report_xml
                xd.sil_goods_sec_1,  # commodities_xml
                None,  # commodities_response_xml
                "ILD1237",  # licence_uref
            ),
            (
                3,  # ima_id
                13,  # imad_id
                3,  # file_folder_id
                "IMA/2022/2346",  # reference
                "COMPLETED",  # status
                dt.datetime(2022, 4, 23, 9),  # submit_datetime
                dt.datetime(2022, 4, 22, 7, 52, 4),  # create_datetime
                dt.datetime(2022, 4, 22, 7, 52, 4),  # created
                1,  # vartiation_no
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                6,  # application_type
                "SILApplication",  # process_type
                "APPROVE",  # decision
                xd.open_variation,  # variations_xml
                dt.datetime(2022, 4, 23, 9),  # last_update_datetime
                1,  # section1
                0,  # section2
                0,  # section5
                1,  # section58_obsolete
                0,  # section58_other
                xd.import_contact_xml,  # bought_from_details_xml
                xd.sr_manual_xml_legacy,  # supplementary_report_xml
                xd.sil_goods_legacy,  # commodities_xml
                None,  # commodities_response_xml
                "ILD123456",  # licence_uref
            ),
        ],
    ),
    queries.ia_type: (
        [
            ("id",),
            ("is_active",),
            ("type",),
            ("sub_type",),
            ("name",),
            ("licence_type_code",),
            ("sigl_flag",),
            ("chief_flag",),
            ("chief_licence_prefix",),
            ("paper_licence_flag",),
            ("electronic_licence_flag",),
            ("cover_letter_flag",),
            ("cover_letter_schedule_flag",),
            ("category_flag",),
            ("default_licence_length_months",),
            ("quantity_unlimited_flag",),
            ("exp_cert_upload_flag",),
            ("supporting_docs_upload_flag",),
            ("multiple_commodities_flag",),
            ("guidance_file_url",),
            ("usage_auto_category_desc_flag",),
            ("case_checklist_flag",),
            ("importer_printable",),
            ("commodity_type_id",),
            ("declaration_template_code_id",),
            ("default_commodity_group_id",),
        ],
        [
            (
                1,  # id
                0,  # is_active
                "TEX",  # type
                "QUOTA",  # sub_type
                "Textiles (Quota)",  # name
                "QUOTA",  # licence_type_code
                "true",  # sigl_flag
                "true",  # chief_flag
                "GBTEX",  # chief_licence_prefix
                "true",  # paper_licence_flag
                "false",  # electronic_licence_flag
                "false",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "false",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "true",  # supporting_docs_upload_flag
                "false",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidence_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_A",  # commodity_type_id
                "IMA_GEN_DECLARATION",  # declaration_template_code_id
                None,  # default_commodity_group_id
            ),
            (
                3,  # id
                0,  # is_active
                "OPT",  # type
                "QUOTA",  # sub_type
                "Outward Processing Trade",  # name
                "OPT",  # licence_type_code
                "true",  # sigl_flag
                "false",  # chief_flag
                None,  # chief_licence_prefix
                "true",  # paper_licence_flag
                "false",  # electronic_licence_flag
                "false",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                9,  # default_licence_length_months
                "false",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "true",  # supporting_docs_upload_flag
                "false",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidence_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_A",  # commodity_type_id
                "IMA_OPT_DECLARATION",  # declaration_template_code_id
                None,  # default_commodity_group_id
            ),
            (
                4,  # id
                0,  # is_active
                "SAN",  # type
                "SAN1",  # sub_type
                "Sanctions and Adhoc Licence Application",  # name
                "SANCTIONS",  # licence_type_code
                "false",  # sigl_flag
                "true",  # chief_flag
                "GBSAN",  # chief_licence_prefix
                "false",  # paper_licence_flag
                "true",  # electronic_licence_flag
                "false",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                None,  # default_licence_length_months
                "false",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "true",  # supporting_docs_upload_flag
                "false",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidence_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                None,  # commodity_type_id
                "IMA_GEN_DECLARATION",  # declaration_template_code_id
                None,  # default_commodity_group_id
            ),
            (
                5,  # id
                1,  # is_active
                "FA",  # type
                "OIL",  # sub_type
                "Firearms and Ammunition (Open Individual Import Licence)",  # name
                "FIREARMS",  # licence_type_code
                "false",  # sigl_flag
                "true",  # chief_flag
                "GBOIL",  # chief_licence_prefix
                "true",  # paper_licence_flag
                "true",  # electronic_licence_flag
                "true",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "true",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "false",  # supporting_docs_upload_flag
                "true",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidance_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_B",  # commodity_type_id
                "IMA_GEN_DECLARATION",  # declaration_template_code_id
                None,  # default_commodity_group_id
            ),
            (
                6,  # id
                1,  # is_active
                "FA",  # type
                "SIL",  # supb_type
                "Firearms and Ammunition (Specific Individual Import Licence)",  # name
                "FIREARMS",  # licence_type_code
                "false",  # sigl_flag
                "true",  # chief_flag
                "GBSIL",  # chief_licence_prefix
                "true",  # paper_licence_flag
                "true",  # electronic_licence_flag
                "true",  # cover_letter_flag
                "true",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "false",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "false",  # supporting_docs_upload_flag
                "true",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidance_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_B",  # commodity_type_id
                "IMA_GEN_DECLARATION",  # declaration_template_code_id
                None,  # default_commodity_group_id
            ),
            (
                9,  # id
                1,  # is_active
                "WD",  # type
                "QUOTA",  # sub_type
                "Wood (Quota)",  # name
                "WOOD",  # licence_type_code
                "true",  # sigl_flag
                "false",  # chief_flag
                None,  # chief_licence_prefix
                "true",  # paper_licence_flag
                "false",  # electronic_licence_flag
                "false",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "false",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "true",  # supporting_docs_upload_flag
                "false",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidence_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_A",  # commodity_type_id
                "IMA_GEN_DECLARATION",  # declaration_template_code_id
                None,  # default_commodity_group_id
            ),
            (
                10,  # id
                1,  # is_active
                "FA",  # type
                "DFL",  # sub_type
                "Firearms and Ammunition (Deactivated Firearms Licence)",  # name
                "FIREARMS",  # licence_type_code
                "false",  # sigl_flag
                "true",  # chief_flag
                "GBDFL",  # chief_licence_prefix
                "true",  # paper_licence_flag
                "true",  # electronic_licence_flag
                "true",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "true",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "false",  # supporting_docs_upload_flag
                "true",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidance_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_B",  # commodity_type_id
                "IMA_GEN_DECLARATION",  # declaration_template_code_id
                None,  # default_commodity_group_id
            ),
            (
                11,  # id
                0,  # is_active
                "SPS",  # type
                "SPS1",  # sub_type
                "Prior Surveillance",  # name
                "SURVEILLANCE",  # licence_type_code
                "false",  # sigl_flag
                "true",  # chief_flag
                "GBAOG",  # chief_licence_prefix
                "true",  # paper_licence_flag
                "true",  # electronic_licence_flag
                "true",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "true",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "false",  # supporting_docs_upload_flag
                "true",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidance_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_B",  # commodity_type_id
                "IMA_GEN_DECLARATION",  # declaration_template_code_id
                None,  # default_commodity_group_id
            ),
            (
                12,  # id
                0,  # is_active
                "ADHOC",  # type
                "ADHOC1",  # sub_type
                "Sanctions and Adhoc Licence Application",  # name
                "ADHOC",  # licence_type_code
                "false",  # sigl_flag
                "true",  # chief_flag
                "GBSAN",  # chief_licence_prefix
                "true",  # paper_licence_flag
                "true",  # electronic_licence_flag
                "true",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "true",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "false",  # supporting_docs_upload_flag
                "true",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidance_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_B",  # commodity_type_id
                "IMA_GEN_DECLARATION",  # declaration_template_code_id
                None,  # default_commodity_group_id
            ),
        ],
    ),
    queries.constabulary_emails: (
        [
            ("ima_id",),
            ("status",),
            ("to",),
            ("cc_address_list_str",),
            ("subject",),
            ("body",),
            ("template_code",),
            ("email_type",),
            ("constabulary_attachments_xml",),
        ],
        [
            (
                1,  # ima_id
                "DRAFT",  # status
                None,  # to
                None,  # cc_address_list_str
                None,  # subject
                None,  # body
                "IMA_CONSTAB_EMAIL",  # template_code
                "CONSTABULARY",  # email_type
                None,  # constabulary_attachments_xml
            ),
            (
                1,  # ima_id
                "OPEN",  # status
                "a@example.com",  # to /PS-IGNORE
                "b@example.com;c@example.com",  # cc_address_list_str /PS-IGNORE
                "test a",  # subject
                "test a body",  # bo
                "IMA_CONSTAB_EMAIL",  # template_code
                "CONSTABULARY",  # email_type
                xd.condtabulary_email_attachments,  # constabulary_attachments_xml
            ),
            (
                1,  # ima_id
                "CLOSED",  # status
                "a@example.com",  # to /PS-IGNORE
                "b@example.com",  # cc_address_list_str /PS-IGNORE
                "test b",  # subject
                "test b body",  # body
                "IMA_CONSTAB_EMAIL",  # template_code
                "CONSTABULARY",  # email_type
                None,  # constabulary_attachments_xml
            ),
        ],
    ),
    queries.case_note: (
        [
            ("ima_id",),
            ("status",),
            ("note",),
            ("created_by_id",),
            ("create_datetime",),
            ("file_folder_id",),
        ],
        [
            (1, "OPEN", "Some note", 2, "2020-01-01T11:12:13", 221),
            (2, "CLOSED", "Some other note", 2, "2021-02-02T12:13:14", 222),
            (2, "DRAFT", "Some draft note", 2, "2022-03-03T13:14:15", 223),
        ],
    ),
    queries.update_request: (
        [
            ("ima_id",),
            ("status",),
            ("request_subject",),
            ("request_detail",),
            ("response_detail",),
            ("request_datetime",),
            ("requested_by_id",),
            ("response_datetime",),
            ("response_by_id",),
            ("closed_datetime",),
            ("closed_by_id",),
        ],
        [
            (
                1,  # ima_id
                "CLOSED",  # status
                "Test Closed",  # request_subject
                "Closed Details",  # request_detail
                "AA",  # response_detail
                dt.datetime(2021, 1, 2, 7),  # request_datetime
                2,  # request_by_id
                dt.datetime(2021, 1, 3, 7),  # response_datetime
                2,  # response_by_id
                dt.datetime(2021, 1, 4, 7),  # closed_datetime
                2,  # closed_by_id
            ),
            (
                1,  # ima_id
                "OPEN",  # status
                "Test Open",  # request_subject
                "Open Details",  # request_detail
                None,  # response_detail
                dt.datetime(2021, 2, 2, 7),  # request_datetime
                2,  # request_by_id
                None,  # response_datetime
                None,  # response_by_id
                None,  # closed_datetime
                None,  # closed_by_id
            ),
            (
                1,  # ima_id
                "DRAFT",  # status
                None,  # request_subject
                None,  # request_detail
                None,  # response_detail
                None,  # request_datetime
                None,  # request_by_id
                None,  # response_datetime
                None,  # response_by_id
                None,  # closed_datetime
                None,  # closed_by_id
            ),
        ],
    ),
    queries.fir: (
        [
            ("ia_ima_id",),
            ("status",),
            ("request_subject",),
            ("request_detail",),
            ("response_details",),
            ("requested_datetime",),
            ("request_by_id",),
            ("response_datetime",),
            ("response_by_id",),
            ("closed_datetime",),
            ("closed_by_id",),
            ("folder_id",),
            ("email_cc_address_list_str",),
            ("process_type",),
            ("created",),
        ],
        [
            (
                1,  # ia_ima_id
                "CLOSED",  # status
                "Test Closed",  # request_subject
                "Closed Details",  # request_detail
                "AA",  # response_detail
                dt.datetime(2021, 1, 2, 12, 23),  # requested_datetime
                2,  # request_by_id
                dt.datetime(2021, 1, 3, 13, 23),  # response_datetime
                2,  # response_by_id
                dt.datetime(2021, 1, 4, 13, 23),  # closed_datetime
                2,  # closed_by_id
                200,  # folder_id
                "b@example.com;c@example.com",  # email_cc_address_list_str /PS-IGNORE
                "FurtherInformationRequest",  # process_type
                dt.datetime(2021, 1, 2, 12, 23),  # created
            ),
            (
                1,  # ia_ima_id
                "RESPONDED",  # status
                "Test Responded",  # request_subject
                "Responded Details",  # request_detail
                "BB",  # response_detail
                dt.datetime(2021, 1, 2, 12, 23),  # requested_datetime
                2,  # request_by_id
                dt.datetime(2021, 1, 3, 13, 23),  # response_datetime
                2,  # response_by_id
                None,  # closed_datetime
                None,  # closed_by_id
                201,  # folder_id
                "b@example.com",  # email_cc_address_list_str /PS-IGNORE
                "FurtherInformationRequest",  # process_type
                dt.datetime(2021, 1, 2, 12, 23),  # created
            ),
            (
                1,  # ia_ima_id
                "OPEN",  # status
                "Test Open",  # request_subject
                "Open Details",  # request_detail
                None,  # response_detail
                dt.datetime(2021, 2, 2, 12, 23),  # requested_datetime
                2,  # request_by_id
                None,  # response_datetime
                None,  # response_by_id
                None,  # closed_datetime
                None,  # closed_by_id
                202,  # folder_id
                None,  # email_cc_address_list_str
                "FurtherInformationRequest",  # process_type
                dt.datetime(2021, 1, 2, 12, 23),  # created
            ),
        ],
    ),
    queries.endorsement: (
        [
            ("imad_id",),
            ("content",),
            ("created_datetime",),
        ],
        [
            (11, "Content A", dt.datetime(2022, 4, 27, 12, 23)),
            (11, "Content B", dt.datetime(2022, 4, 27, 12, 23)),
        ],
    ),
    queries.sigl_transmission: (
        [
            ("ima_id",),
            ("status",),
            ("transmission_type",),
            ("request_type",),
            ("sent_datetime",),
            ("sent_by_id",),
            ("response_datetime",),
            ("response_message",),
            ("response_code",),
        ],
        [
            (
                100,  # ima_id
                "ACCEPTED",  # status
                "WEB_SERVICE",  # transmission_type
                "INSERT",  # request_type
                dt.datetime.now(),  # sent_datetime
                2,  # sent_by_id
                dt.datetime.now(),  # response_datetime
                "Successful processing",  # response_message
                0,  # response_code
            ),
            (
                100,  # ima_id
                "ACCEPTED",  # status
                "WEB_SERVICE",  # transmission_type
                "CONFIRM",  # request_type
                dt.datetime.now(),  # sent_datetime
                2,  # sent_by_id
                dt.datetime.now(),  # response_datetime
                "Successful processing",  # response_message
                0,  # response_code
            ),
            (
                100,  # ima_id
                "ACCEPTED",  # status
                "WEB_SERVICE",  # transmission_type
                "DELETE",  # request_type
                dt.datetime.now(),  # sent_datetime
                2,  # sent_by_id
                dt.datetime.now(),  # response_datetime
                "Successful processing",  # response_message
                0,  # response_code
            ),
            (
                101,  # ima_id
                "REJECTED",  # status
                "MANUAL",  # transmission_type
                "INSERT",  # request_type
                dt.datetime.now(),  # sent_datetime
                2,  # sent_by_id
                dt.datetime.now(),  # response_datetime
                "Something missing",  # response_message
                500,  # response_code
            ),
            (
                101,  # ima_id
                "ACCEPTED",  # status
                "MANUAL",  # transmission_type
                "INSERT",  # request_type
                dt.datetime.now(),  # sent_datetime
                2,  # sent_by_id
                None,  # response_datetime
                None,  # response_message
                None,  # response_code
            ),
        ],
    ),
}
