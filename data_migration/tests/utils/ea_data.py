import datetime as dt

from data_migration import queries

from . import xml_data as xd

EA_BASE_COLUMNS = [
    ("ca_id",),
    ("cad_id",),
    ("process_type",),
    ("reference",),
    ("status",),
    ("created_by_id",),
    ("create_datetime",),
    ("created",),
    ("submit_datetime",),
    ("last_updated_by_id",),
    ("last_update_datetime",),
    ("variation_no",),
    ("application_type_id",),
    ("exporter_id",),
    ("exporter_office_legacy_id",),
    ("case_note_xml",),
    ("fir_xml",),
    ("update_request_xml",),
    ("variations_xml",),
]


ea_query_result = {
    queries.product_legislation: (
        [
            ("id",),
            ("name",),
            ("is_active",),
            ("is_biocidal",),
            ("is_biocidal_claim",),
            ("is_eu_cosmetics_regulation",),
            ("gb_legislation",),
            ("ni_legislation",),
        ],
        [
            (
                1,  # id
                "Test",  # name
                1,  # is_active
                0,  # is_biocidal
                0,  # is_biocidal_claim
                1,  # is_eu_cosmetics_regulation
                1,  # gb_legislation
                1,  # ni_legislation
            ),
            (
                2,  # id
                "Test Biocide",  # name
                1,  # is_active
                1,  # is_biocidal
                0,  # is_biocidal_claim
                0,  # is_eu_cosmetics_regulation
                1,  # gb_legislation
                0,  # ni_legislation
            ),
            (
                3,  # id
                "Test Inactive",  # name
                0,  # is_active
                0,  # is_biocidal
                0,  # is_biocidal_claim
                0,  # is_eu_cosmetics_regulation
                0,  # gb_legislation
                1,  # ni_legislation
            ),
        ],
    ),
    queries.export_application_type: (
        [
            ("id",),
            ("is_active",),
            ("type_code",),
            ("type",),
            ("allow_multiple_products",),
            ("generate_cover_letter",),
            ("allow_hse_authorization",),
            ("country_group_legacy_id",),
            ("country_of_manufacture_cg_id",),
        ],
        [
            (1, 1, "CFS", "Certificate of Free Sale", 1, 0, 0, "A", None),
            (2, 1, "COM", "Certificate of Manufacture", 0, 0, 0, "B", None),
            (21, 1, "GMP", "Certificate of Good Manufacturing Practice", 1, 0, 0, "C", None),
        ],
    ),
    queries.gmp_application: (
        EA_BASE_COLUMNS
        + [
            ("responsible_address_type",),
            ("manufacturer_address_type",),
            ("brand_name",),
            ("file_folder_id",),
            ("gmp_certificate_issued",),
            ("withdrawal_xml",),
            ("is_responsible_person",),
            ("responsible_person_name",),
            ("responsible_person_address",),
            ("responsible_person_country",),
            ("responsible_person_postcode",),
            ("auditor_accredited",),
            ("auditor_certified",),
            ("submitted_by_id",),
            ("decision",),
            ("is_manufacturer",),
            ("manufacturer_name",),
            ("manufacturer_address",),
            ("manufacturer_country",),
            ("manufacturer_postcode",),
        ],
        [
            (
                7,  # ca_id
                17,  # cad_id
                "CertificateofGoodManufacturingPractice",  # process_type
                "GA/2022/9901",  # reference
                "IN PROGRESS",  # status
                2,  # created_by_id
                dt.datetime(2022, 4, 27),  # create_datetime
                dt.datetime(2022, 4, 27),  # created
                None,  # submit_datetime
                2,  # last_updated_by_id
                dt.datetime(2022, 4, 27),  # last_updated_datetime
                0,  # variation_no
                21,  # application_type_id
                2,  # exporter_id
                "e-2-1",  # export_office_legacy_id
                None,  # case_note_xml
                None,  # fir_xml
                None,  # update_request_xml
                None,  # variations_xml
                "SEARCH",  # responsible_address_type
                "SEARCH",  # manufacturer_address_type
                None,  # brand_name
                231,  # file_folder_id
                None,  # gmp_certificate_issued
                None,  # withdrawal_xml
                None,  # is_responsible_person
                None,  # responsible_person_name
                None,  # responsible_person_address
                None,  # responsible_person_country
                None,  # responsible_person_postcode
                None,  # auditor accredited
                None,  # auditor certified
                None,  # submitted by id
                None,  # decision
                None,  # is_manufacturer
                None,  # manufacturer_name
                None,  # manufacturer_address
                None,  # manufacturer_country
                None,  # manufacturer_postcode
            ),
            (
                8,
                18,
                "CertificateofGoodManufacturingPractice",
                "GA/2022/9902",
                "PROCESSING",
                2,
                dt.datetime(2022, 4, 28),
                dt.datetime(2022, 4, 28),
                dt.datetime(2022, 4, 29),
                2,
                dt.datetime(2022, 4, 29),
                0,
                21,
                3,
                "e-3-1",
                xd.export_case_note_1,
                None,  # fir_xml
                xd.export_update_xml_1,  # update_request_xml
                None,  # variations_xml
                "EMPTY",  # responsible_person_address_type
                "MANUAL",  # manufacturer_address_type
                "A brand",
                232,
                "BRCGS",  # gmp_certificate_issued
                None,  # withdrawal_xml
                "no",  # is_responsible_person
                None,  # responsible_person_name
                None,  # responsible_person_address
                None,  # responsible_person_country
                None,  # responsible_person_postcode
                "no",  # auditor accredited
                None,  # auditor certified
                None,  # submitted by id
                None,  # decision
                "no",  # is_manufacturer
                None,  # manufacturer_name
                None,  # manufacturer_address
                None,  # manufacturer_country
                None,  # manufacturer_postcode
            ),
            (
                9,
                19,
                "CertificateofGoodManufacturingPractice",
                "GA/2022/9903",
                "COMPLETED",
                2,
                dt.datetime(2022, 4, 28),
                dt.datetime(2022, 4, 28),
                dt.datetime(2022, 4, 29),
                2,
                dt.datetime(2022, 4, 29),
                1,
                21,
                2,
                "e-2-2",
                None,  # case_note_xml
                None,  # fir_xml
                None,  # update_request_xml
                xd.export_varation_1,  # variations_xml
                "MANUAL",  # responsible_person_address_type
                "MANUAL",  # manufacturer_address_type
                "Another brand",
                233,  # file_folder_id
                "ISO22716",  # gmp_certificate_issued
                None,  # withdrawal_xml
                "yes",  # is_responsible_person
                "G. M. Potter",  # responsible_person_name
                "The Bridge\nLondon",  # responsible_person_address
                "GB",  # responsible_person_country
                "12345",  # responsible_person_postcode
                "yes",  # auditor accredited
                "yes",  # auditor certified
                2,  # submitted by id
                "APPROVE",  # decision
                "yes",  # is_manufacturer
                "Cars",  # manufacturer_name
                "The Street\nLondon",  # manufacturer_address
                "GB",  # manufacturer_country
                "12345",  # manufacturer_postcode
            ),
            (
                16,  # ca_id
                26,  # cad_id
                "CertificateofGoodManufacturingPractice",  # process_type
                "GA/2022/9910",  # reference
                "WITHDRAWN",  # status
                2,  # created_by_id
                dt.datetime(2022, 4, 28),  # create_datetime
                dt.datetime(2022, 4, 28),  # created
                dt.datetime(2022, 4, 29),  # submit_datetime
                2,  # last_updated_by_id
                dt.datetime(2022, 4, 29),  # last_updated_datetime
                0,  # variation_id
                21,  # application_type_id
                2,  # exporter_id
                "e-2-2",  # exporter_office_legacy_id
                None,  # case_note_xml
                None,  # fir_xml
                None,  # update_request_xml
                None,  # variations_xml
                "MANUAL",  # responsible_person_address_type
                "MANUAL",  # manufacturer_address_type
                "Test brand",  # brand_name
                234,  # file_folder_id
                "ISO22716",  # gmp_certificate_issued
                xd.export_withdrawal,  # withdrawal_xml
                None,  # is_responsible_person
                None,  # responsible_person_name
                None,  # responsible_person_address
                None,  # responsible_person_country
                None,  # responsible_person_postcode
                None,  # auditor accredited
                None,  # auditor certified
                None,  # submitted by id
                "REFUSE",  # decision
                None,  # is_manufacturer
                None,  # manufacturer_name
                None,  # manufacturer_address
                None,  # manufacturer_country
                None,  # manufacturer_postcode
            ),
            (
                17,
                27,
                "CertificateofGoodManufacturingPractice",
                "GA/2022/9911",
                "COMPLETED",
                2,
                dt.datetime(2022, 4, 28),
                dt.datetime(2022, 4, 28),
                dt.datetime(2022, 5, 29),
                2,
                dt.datetime(2022, 5, 29),
                1,
                21,
                2,
                "e-2-2",
                None,  # case_note_xml
                None,  # fir_xml
                None,  # update_request_xml
                xd.export_varation_1,  # variations_xml
                "MANUAL",  # responsible_person_address_type
                "MANUAL",  # manufacturer_address_type
                "Another brand",
                233,  # file_folder_id
                "ISO22716",  # gmp_certificate_issued
                None,  # withdrawal_xml
                "yes",  # is_responsible_person
                "G. M. Potter",  # responsible_person_name
                "The Bridge\nLondon",  # responsible_person_address
                "GB",  # responsible_person_country
                "12345",  # responsible_person_postcode
                "yes",  # auditor accredited
                "yes",  # auditor certified
                2,  # submitted by id
                "APPROVE",  # decision
                "yes",  # is_manufacturer
                "Cars",  # manufacturer_name
                "The Street\nLondon",  # manufacturer_address
                "GB",  # manufacturer_country
                "12345",  # manufacturer_postcode
            ),
        ],
    ),
    queries.export_application_countries: (
        [("cad_id",), ("country_id",)],
        [(18, 1), (18, 2), (18, 3), (19, 1), (21, 1), (22, 1), (24, 1), (25, 1)],
    ),
    queries.com_application: (
        EA_BASE_COLUMNS
        + [
            ("is_pesticide_on_free_sale_uk",),
            ("is_manufacturer",),
            ("product_name",),
            ("chemical_name",),
            ("manufacturing_process",),
        ],
        [
            (
                10,  # ca_id
                20,  # cad_id
                "CertificateOfManufactureApplication",  # process_type
                "CA/2022/9904",  # reference
                "IN PROGRESS",  # status
                2,  # created_by_id
                dt.datetime(2022, 4, 27),  # create_datetime
                dt.datetime(2022, 4, 27),  # created
                None,  # submit_datetime
                2,  # last_updated_by_id
                dt.datetime(2022, 4, 27),  # last_update_datetime
                0,  # variation_no
                2,  # application_type_id
                2,  # exporter_id
                "e-2-1",  # export_office_legacy_id
                None,  # case_note_xml
                None,  # fir_xml
                None,  # update_request_xml
                None,  # variations_xml
                None,  # is_pesticide_on_free_sale_uk
                None,  # is_manufacturer
                None,  # product_name
                None,  # chemical_name
                None,  # manufacturing_process
            ),
            (
                11,
                21,
                "CertificateOfManufactureApplication",
                "CA/2022/9905",
                "PROCESSING",
                2,
                dt.datetime(2022, 4, 28),
                dt.datetime(2022, 4, 28),
                dt.datetime(2022, 4, 29),
                2,
                dt.datetime(2022, 4, 29),
                0,
                2,
                3,
                "e-3-1",
                None,  # case_note_xml
                None,  # fir_xml
                xd.export_update_xml_2,  # update_request_xml
                None,  # variations_xml
                1,  # is_pesticide_on_free_sale_uk
                0,  # is_manufacturer
                "A product",  # product_name
                "A chemical",  # chemical_name
                "Test",  # manufacturing_process
            ),
            (
                12,
                22,
                "CertificateOfManufactureApplication",
                "CA/2022/9906",
                "COMPLETED",
                2,
                dt.datetime(2022, 4, 28),
                dt.datetime(2022, 4, 28),
                dt.datetime(2022, 4, 29),
                2,
                dt.datetime(2022, 4, 29),
                0,
                2,
                2,
                "e-2-2",
                None,  # case_note_xml
                xd.export_fir_xml_1,  # fir_xml
                None,  # update_request_xml
                None,  # variations_xml
                0,  # is_pesticide_on_free_sale_uk
                1,  # is_manufacturer
                "Another product",  # product_name
                "Another chemical",  # chemical_name
                "Test process",  # manufacturing_process
            ),
        ],
    ),
    queries.cfs_application: (
        EA_BASE_COLUMNS,
        [
            (
                13,  # ca_id
                23,  # cad_id
                "CertificateOfFreeSaleApplication",  # process_type
                "CA/2022/9907",  # reference
                "IN PROGRESS",  # status
                2,  # created_by_id
                dt.datetime(2022, 4, 27),  # create_datetime
                dt.datetime(2022, 4, 27),  # created
                None,  # submit_datetime
                2,  # last_updated_by_id
                dt.datetime(2022, 4, 27),  # last_update_datetime
                0,  # variation_no
                2,  # application_type_id
                2,  # exporter_id
                "e-2-1",  # export_office_legacy_id
                None,  # case_note_xml
                None,  # fir_xml
                None,  # update_request_xml
                None,  # variations_xml
            ),
            (
                14,  # ca_id
                24,  # cad_id
                "CertificateOfFreeSaleApplication",  # process_type
                "CA/2022/9908",  # reference
                "PROCESSING",  # status
                2,  # created_by_id
                dt.datetime(2022, 4, 28),  # create_datetime
                dt.datetime(2022, 4, 28),  # created
                dt.datetime(2022, 4, 29),  # submit_datetime
                2,  # last_updated_by_id
                dt.datetime(2022, 4, 29),  # last_update_datetime
                0,  # variation_no
                2,  # application_type_id
                3,  # exporter_id
                "e-3-1",  # export_office_legacy_id
                None,  # case_note_xml
                xd.export_fir_xml_2,  # fir_xml
                None,  # update_request_xml
                None,  # variations_xml
            ),
            (
                15,  # ca_id
                25,  # cad_id
                "CertificateOfFreeSaleApplication",  # process_type
                "CA/2022/9909",  # reference
                "COMPLETED",  # status
                2,  # created_by_id
                dt.datetime(2022, 4, 28),  # create_datetime
                dt.datetime(2022, 4, 28),  # created
                dt.datetime(2022, 4, 29),  # submit_datetime
                2,  # last_updated_by_id
                dt.datetime(2022, 4, 29),  # last_update_datetime
                2,  # variation_no
                2,  # application_type_id
                2,  # exporter_id
                "e-2-2",  # export_office_legacy_id
                xd.export_case_note_2,  # case_note_xml
                None,  # fir_xml
                None,  # update_request_xml
                xd.export_varation_2,  # variations_xml
            ),
        ],
    ),
    queries.cfs_schedule: (
        [
            ("cad_id",),
            ("schedule_ordinal",),
            ("exporter_status",),
            ("brand_name_holder",),
            ("product_eligibility",),
            ("goods_placed_on_uk_market",),
            ("goods_export_only",),
            ("any_raw_materials",),
            ("final_product_end_use",),
            ("country_of_manufacture_id",),
            ("accordance_with_standards",),
            ("is_responsible_person",),
            ("manufacturer_name",),
            ("manufacturer_address_type",),
            ("created_by_id",),
            ("created_at",),
            ("updated_at",),
            ("product_xml",),
            ("legislation_xml",),
        ],
        [
            (
                24,  # cad_id
                1,  # schedule_ordinal
                "MANUFACTURER",  # exporter_status
                None,  # brand_name_holder
                "ON_SALE",  # product_eligibility
                "no",  # goods_placed_on_uk_market
                "yes",  # goods_export_only
                "no",  # any_raw_materials
                None,  # final_product_end_use
                1,  # country_of_manufacture_id
                1,  # accordance_with_standards
                0,  # is_repsonsible_person
                "Manufacturer",  # manufacturer_name
                "SEARCH",  # manufacturer_address_type
                2,  # created_by_id
                dt.datetime(2022, 11, 1, 12, 30),  # created_at
                dt.datetime(2022, 11, 1, 12, 30),  # updated_at
                xd.cfs_product,  # product_xml
                None,  # legislation_xml
            ),
            (
                25,  # cad_id
                1,  # schedule_ordinal
                "NOT_MANUFACTURER",  # exporter_status
                "yes",  # brand_name_holder
                "MAY_BE_SOLD",  # product_eligibility
                "yes",  # goods_placed_on_uk_market
                "no",  # goods_export_only
                "yes",  # any_raw_materials
                "A product",  # final_product_end_use
                1,  # country_of_manufacture_id
                0,  # accordance_with_standards
                1,  # is_repsonsible_person
                None,  # manufacturer_name
                "SEARCH",  # manufacturer_address_type
                2,  # created_by_id
                dt.datetime(2022, 11, 1, 12, 30),  # created_at
                dt.datetime(2022, 11, 1, 12, 30),  # updated_at
                None,  # product_xml
                xd.cfs_legislation,  # legislation_xml
            ),
            (
                25,  # cad_id
                2,  # schedule_ordinal
                "MANUFACTURER",  # exporter_status
                "no",  # brand_name_holder
                "ON_SALE",  # product_eligibility
                "no",  # goods_placed_on_uk_market
                "yes",  # goods_export_only
                "no",  # any_raw_materials
                None,  # final_product_end_use
                1,  # country_of_manufacture_id
                1,  # accordance_with_standards
                0,  # is_repsonsible_person
                "Manufacturer",  # manufacturer_name
                "SEARCH",  # manufacturer_address_type
                2,  # created_by_id
                dt.datetime(2022, 11, 1, 12, 30),  # created_at
                dt.datetime(2022, 11, 1, 12, 30),  # updated_at
                xd.cfs_product_biocide,  # product_xml
                xd.cfs_legislation_biocide,  # legislation_xml
            ),
        ],
    ),
    queries.export_certificate: (
        [
            ("ca_id",),
            ("cad_id",),
            ("case_completion_datetime",),
            ("status",),
            ("case_reference",),
            ("created_at",),
            ("updated_at",),
            ("document_pack_id",),
            ("revoke_reason",),
            ("revoke_email_sent",),
        ],
        [
            (
                8,  # ca_id
                18,  # cad_id
                None,  # case_completion_datetime
                "DR",  # status
                "GA/2022/9902",  # case_reference
                dt.datetime(2022, 4, 29, 13, 21),  # created_at
                dt.datetime(2022, 4, 29, 13, 21),  # updated_at
                20,  # document_pack_id
                None,  # revoke reason
                False,  # revoke email sent
            ),
            (
                9,
                10,
                dt.datetime(2022, 4, 29),
                "AR",
                "GA/2022/9903",
                dt.datetime(2022, 4, 29, 13, 21),
                dt.datetime(2022, 4, 29, 13, 21),
                21,
            ),
            (
                9,
                19,
                dt.datetime(2022, 4, 29),
                "AC",
                "CA/2022/9903/1",
                dt.datetime(2022, 4, 29, 13, 21),
                dt.datetime(2022, 4, 29, 13, 21),
                22,
                None,
                False,
            ),
            (
                11,
                21,
                None,
                "DR",
                "CA/2022/9905",
                dt.datetime(2022, 4, 29, 13, 21),
                dt.datetime(2022, 4, 29, 13, 21),
                23,
                None,
                False,
            ),
            (
                12,
                22,
                dt.datetime(2022, 4, 29),
                "AC",
                "CA/2022/9906",
                dt.datetime(2022, 4, 29, 13, 21),
                dt.datetime(2022, 4, 29, 13, 21),
                24,
                None,
                False,
            ),
            (
                14,
                24,
                dt.datetime(2022, 4, 29),
                "DR",
                "CA/2022/9908",
                dt.datetime(2022, 4, 29, 13, 21),
                dt.datetime(2022, 4, 29, 13, 21),
                25,
                None,
                False,
            ),
            (
                15,
                11,
                dt.datetime(2022, 4, 29),
                "AR",
                "CA/2022/9909",
                dt.datetime(2022, 4, 29, 13, 21),
                dt.datetime(2022, 4, 29, 13, 21),
                26,
                None,
                False,
            ),
            (
                15,
                12,
                dt.datetime(2022, 4, 29),
                "AR",
                "CA/2022/9909/1",
                dt.datetime(2022, 4, 29, 13, 21),
                dt.datetime(2022, 4, 29, 13, 21),
                27,
                None,
                False,
            ),
            (
                15,
                25,
                dt.datetime(2022, 4, 29),
                "AC",
                "CA/2022/9909/2",
                dt.datetime(2022, 4, 29, 13, 21),
                dt.datetime(2022, 4, 29, 13, 21),
                28,
                None,
                False,
            ),
            (
                9,
                26,
                dt.datetime(2022, 4, 29),
                "RE",
                "GA/2022/9909",
                dt.datetime(2022, 4, 29, 13, 21),
                dt.datetime(2022, 4, 29, 13, 21),
                29,
                "No longer trading",
                True,
            ),
        ],
    ),
    queries.export_document_pack_acknowledged: (
        [("exportcertificate_id",), ("user_id",)],
        [(24, 2), (27, 2), (28, 2), (28, 6)],
    ),
    queries.export_certificate_docs: (
        [
            ("cad_id",),
            ("certificate_id",),
            ("document_legacy_id",),
            ("reference",),
            ("case_document_ref_id",),
            ("document_type",),
            ("country_id",),
            ("filename",),
            ("content_type",),
            ("file_size",),
            ("path",),
            ("created_datetime",),
            ("created_by_id",),
            ("check_code",),
            ("prefix",),
            ("year",),
            ("reference_no",),
        ],
        [
            (
                18,  # cad_id
                1,  # certificate_id
                101,  # document_legacy_id
                "GMP/2022/00001",  # reference
                "GMP/2022/00001",  # case_document_ref_id
                "CERTIFICATE",  # document_type
                1,  # country_id
                "gmp-cert-1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-1.pdf",  # path
                dt.datetime(2024, 1, 1, 10, 10),  # created_datetime
                2,  # created_by_id
                12345678,  # check_code
                "GMP",  # prefix
                2022,  # year
                1,  # reference_no
            ),
            (
                18,  # cad_id
                2,  # certificate_id
                102,  # document_legacy_id
                "GMP/2022/00002",  # reference
                "GMP/2022/00002",  # case_document_ref_id
                "CERTIFICATE",  # document_type
                2,  # country_id
                "gmp-cert-2.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-2.pdf",  # path
                dt.datetime(2024, 1, 1, 10, 10),  # created_datetime
                2,  # created_by_id
                56781234,  # check_code
                "GMP",  # prefix
                2022,  # year
                2,  # reference_no
            ),
            (
                18,  # cad_id
                3,  # certificate_id
                103,  # document_legacy_id
                "GMP/2022/00003",  # reference
                "GMP/2022/00003",  # case_document_ref_id
                "CERTIFICATE",  # document_type
                3,  # country_id
                "gmp-cert-3.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-3.pdf",  # path
                dt.datetime(2024, 1, 1, 10, 10),  # created_datetime
                2,  # created_by_id
                43215678,  # check_code
                "GMP",  # prefix
                2022,  # year
                3,  # reference_no
            ),
            (
                19,  # cad_id
                4,  # certificate_id
                104,  # document_legacy_id
                "GMP/2022/00004",  # reference
                "GMP/2022/00004",  # case_document_ref_id
                "CERTIFICATE",  # document_type
                1,  # country_id
                "gmp-cert-4.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-4.pdf",  # path
                dt.datetime(2024, 1, 1, 10, 10),  # created_datetime
                2,  # created_by_id
                87654321,  # check_code
                "GMP",  # prefix
                2022,  # year
                4,  # reference_no
            ),
            (
                21,  # cad_id
                5,  # certificate_id
                105,  # document_legacy_id
                "COM/2022/00001",  # reference
                "COM/2022/00001",  # case_document_ref_id
                "CERTIFICATE",  # document_type
                1,  # country_id
                "com-cert-1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/com-cert-1.pdf",  # path
                dt.datetime.now(),  # created_datetime
                2,  # created_by_id
                87651432,  # check_code
                "COM",  # prefix
                2022,  # year
                1,  # reference_no
            ),
            (
                22,  # cad_id
                6,  # certificate_id
                106,  # document_legacy_id
                "COM/2022/00002",  # reference
                "COM/2022/00002",  # case_document_ref_id
                "CERTIFICATE",  # document_type
                1,  # country_id
                "com-cert-2.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/com-cert-2.pdf",  # path
                dt.datetime.now(),  # created_datetime
                2,  # created_by_id
                87651432,  # check_code
                "COM",  # prefix
                2022,  # year
                2,  # reference_no
            ),
            (
                24,  # cad_id
                7,  # certificate_id
                107,  # document_legacy_id
                "CFS/2022/00001",  # reference
                "CFS/2022/00001",  # case_document_ref_id
                "CERTIFICATE",  # document_type
                1,  # country_id
                "cfs-cert-1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/cfs-cert-1.pdf",  # path
                dt.datetime.now(),  # created_datetime
                2,  # created_by_id
                32415678,  # check_code
                "CFS",  # prefix
                2022,  # year
                1,  # reference_no
            ),
            (
                25,  # cad_id
                8,  # certificate_id
                108,  # document_legacy_id
                "CFS/2022/00002",  # reference
                "CFS/2022/00002",  # case_document_ref_id
                "CERTIFICATE",  # document_type
                1,  # country_id
                "cfs-cert-2.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/cfs-cert-2.pdf",  # path
                dt.datetime.now(),  # created_datetime
                2,  # created_by_id
                32415679,  # check_code
                "CFS",  # prefix
                2022,  # year
                2,  # reference_no
            ),
            (
                26,  # cad_id
                9,  # certificate_id
                109,  # document_legacy_id
                "GMP/2022/00005",  # reference
                "GMP/2022/00005",  # case_document_ref_id
                "CERTIFICATE",  # document_type
                1,  # country_id
                "gmp-cert-5.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-5.pdf",  # path
                dt.datetime(2024, 1, 1, 10, 10),  # created_datetime
                2,  # created_by_id
                87654355,  # check_code
                "GMP",  # prefix
                2022,  # year
                5,  # reference_no
            ),
        ],
    ),
    queries.beis_emails: (
        [
            ("ca_id",),
            ("status",),
            ("to",),
            ("subject",),
            ("body",),
            ("response",),
            ("sent_datetime",),
            ("closed_datetime",),
            ("template_code",),
        ],
        [
            (
                9,  # ca_id
                "CLOSED",  # status
                "a@example.com",  # to /PS-IGNORE
                "subject",  # subject
                "body",  # body
                "response",  # response
                dt.datetime.now(),  # sent_datetime
                dt.datetime.now(),  # closed_datetime
                "CA_BEIS_EMAIL",  # template_code
            ),
            (
                9,  # ca_id
                "OPEN",  # status
                "a@example.com",  # to /PS-IGNORE
                "subject",  # subject
                "body",  # body
                None,  # response
                dt.datetime.now(),  # sent_datetime
                None,  # closed_datetime
                "CA_BEIS_EMAIL",  # template_code
            ),
        ],
    ),
    queries.hse_emails: (
        [
            ("ca_id",),
            ("status",),
            ("to",),
            ("subject",),
            ("body",),
            ("response",),
            ("sent_datetime",),
            ("closed_datetime",),
        ],
        [
            (
                15,  # ca_id
                "CLOSED",  # status
                "a@example.com",  # to /PS-IGNORE
                "subject",  # subject
                "body",  # body
                "response",  # response
                dt.datetime.now(),  # sent_datetime
                dt.datetime.now(),  # closed_datetime
                "CA_HSE_EMAIL",  # template_code
            ),
            (
                15,  # ca_id
                "OPEN",  # status
                "a@example.com",  # to /PS-IGNORE
                "subject",  # subject
                "body",  # body
                None,  # response
                dt.datetime.now(),  # sent_datetime
                None,  # closed_datetime
                "CA_HSE_EMAIL",  # template_code
            ),
        ],
    ),
    queries.export_application_template: (
        [
            ("id",),
            ("name",),
            ("description",),
            ("application_type",),
            ("sharing",),
            ("owner_id",),
            ("created_datetime",),
            ("last_updated_datetime",),
            ("is_active",),
        ],
        [
            (
                1,  # id
                "Template CFS",  # name
                "A CFS Template",  # description
                "CFS",  # application_type
                "PRIVATE",  # sharing
                2,  # owner_id
                dt.datetime(2023, 1, 2, 13, 23),  # created_datetime
                dt.datetime(2023, 1, 2, 14, 23),  # last_updated_datetime
                1,  # is_active
            ),
            (
                2,  # id
                "Template COM",  # name
                "A COM Template",  # description
                "COM",  # application_type
                "EDIT",  # sharing
                2,  # owner_id
                dt.datetime(2023, 1, 3, 13, 23),  # create_datetime
                dt.datetime(2023, 1, 3, 14, 23),  # last_updated_datetime
                1,  # is_active
            ),
        ],
    ),
    queries.cfs_application_template: (
        [
            ("id",),
            ("template_id",),
            ("countries_xml",),
            ("schedules_xml",),
        ],
        [
            (
                1,  # id
                1,  # template_id
                xd.cat_countries_xml,  # countries_xml
                xd.cfs_schedule_template_xml,  # schedules_xml
            ),
        ],
    ),
    queries.com_application_template: (
        [
            ("template_id",),
            ("is_free_sale_uk",),
            ("is_manufacturer",),
            ("product_name",),
            ("chemical_name",),
            ("manufacturing_process",),
            ("countries_xml",),
        ],
        [
            (
                1,  # template_id
                False,  # is_free_sale_uk
                True,  # is_manufacturer
                "Test product",  # product_name
                "Test chemical",  # chemical_name
                "Test manufacturing process",  # test_manufacturing_process
                xd.cat_countries_xml,  # countries_xml
            ),
        ],
    ),
}
