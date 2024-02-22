from datetime import datetime

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
    ("last_updated_datetime",),
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
            ("country_of_manufacture_cg_id"),
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
            ("brand_name",),
            ("file_folder_id",),
            ("gmp_certificate_issued",),
            ("withdrawal_xml",),
        ],
        [
            (
                7,  # ca_id
                17,  # cad_id
                "CertificateofGoodManufacturingPractice",  # process_type
                "GA/2022/9901",  # reference
                "IN PROGRESS",  # status
                2,  # created_by_id
                datetime(2022, 4, 27),  # create_datetime
                datetime(2022, 4, 27),  # created
                None,  # submit_datetime
                2,  # last_updated_by_id
                datetime(2022, 4, 27),  # last_updated_datetime
                0,  # variation_no
                21,  # application_type_id
                2,  # exporter_id
                "e-2-1",  # export_office_legacy_id
                None,  # case_note_xml
                None,  # fir_xml
                None,  # update_request_xml
                None,  # variations_xml
                None,  # brand_name
                231,  # file_folder_id
                None,  # gmp_certificate_issued
                None,  # withdrawal_xml
            ),
            (
                8,
                18,
                "CertificateofGoodManufacturingPractice",
                "GA/2022/9902",
                "PROCESSING",
                2,
                datetime(2022, 4, 28),
                datetime(2022, 4, 28),
                datetime(2022, 4, 29),
                2,
                datetime(2022, 4, 29),
                0,
                21,
                3,
                "e-3-1",
                xd.export_case_note_1,
                None,  # fir_xml
                xd.export_update_xml_1,  # update_request_xml
                None,  # variations_xml
                "A brand",
                232,
                "BRCGS",  # gmp_certificate_issued
                None,  # withdrawal_xml
            ),
            (
                9,
                19,
                "CertificateofGoodManufacturingPractice",
                "GA/2022/9903",
                "COMPLETED",
                2,
                datetime(2022, 4, 28),
                datetime(2022, 4, 28),
                datetime(2022, 4, 29),
                2,
                datetime(2022, 4, 29),
                1,
                21,
                2,
                "e-2-2",
                None,  # case_note_xml
                None,  # fir_xml
                None,  # update_request_xml
                xd.export_varation_1,  # variations_xml
                "Another brand",
                233,  # file_folder_id
                "ISO22716",  # gmp_certificate_issued
                None,  # withdrawal_xml
            ),
            (
                16,  # ca_id
                26,  # cad_id
                "CertificateofGoodManufacturingPractice",  # process_type
                "GA/2022/9910",  # reference
                "WITHDRAWN",  # status
                2,  # created_by_id
                datetime(2022, 4, 28),  # create_datetime
                datetime(2022, 4, 28),  # created
                datetime(2022, 4, 29),  # submit_datetime
                2,  # last_updated_by_id
                datetime(2022, 4, 29),  # last_updated_datetime
                0,  # variation_id
                21,  # application_type_id
                2,  # exporter_id
                "e-2-2",  # exporter_office_legacy_id
                None,  # case_note_xml
                None,  # fir_xml
                None,  # update_request_xml
                None,  # variations_xml
                "Test brand",  # brand_name
                234,  # file_folder_id
                "ISO22716",  # gmp_certificate_issued
                xd.export_withdrawal,  # withdrawal_xml
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
                datetime(2022, 4, 27),  # create_datetime
                datetime(2022, 4, 27),  # created
                None,  # submit_datetime
                2,  # last_updated_by_id
                datetime(2022, 4, 27),  # last_updated_datetime
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
                datetime(2022, 4, 28),
                datetime(2022, 4, 28),
                datetime(2022, 4, 29),
                2,
                datetime(2022, 4, 29),
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
                datetime(2022, 4, 28),
                datetime(2022, 4, 28),
                datetime(2022, 4, 29),
                2,
                datetime(2022, 4, 29),
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
                datetime(2022, 4, 27),  # create_datetime
                datetime(2022, 4, 27),  # created
                None,  # submit_datetime
                2,  # last_updated_by_id
                datetime(2022, 4, 27),  # last_updated_datetime
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
                datetime(2022, 4, 28),  # create_datetime
                datetime(2022, 4, 28),  # created
                datetime(2022, 4, 29),  # submit_datetime
                2,  # last_updated_by_id
                datetime(2022, 4, 29),  # last_updated_datetime
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
                datetime(2022, 4, 28),  # create_datetime
                datetime(2022, 4, 28),  # created
                datetime(2022, 4, 29),  # submit_datetime
                2,  # last_updated_by_id
                datetime(2022, 4, 29),  # last_updated_datetime
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
                "MANUAL",  # manufacturer_address_type
                2,  # created_by_id
                datetime(2022, 11, 1, 12, 30),  # created_at
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
                "MANUAL",  # manufacturer_address_type
                2,  # created_by_id
                datetime(2022, 11, 1, 12, 30),  # created_at
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
                "MANUAL",  # manufacturer_address_type
                2,  # created_by_id
                datetime(2022, 11, 1, 12, 30),  # created_at
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
            ("document_pack_id",),
        ],
        [
            (
                8,
                18,
                datetime(2022, 4, 29),
                "DR",
                "GA/2022/9902",
                datetime(2022, 4, 29, 13, 21),
                20,
            ),
            (
                9,
                10,
                datetime(2022, 4, 29),
                "AR",
                "GA/2022/9903",
                datetime(2022, 4, 29, 13, 21),
                21,
            ),
            (
                9,
                19,
                datetime(2022, 4, 29),
                "AC",
                "CA/2022/9903/1",
                datetime(2022, 4, 29, 13, 21),
                22,
            ),
            (
                11,
                21,
                datetime(2022, 4, 29),
                "DR",
                "CA/2022/9905",
                datetime(2022, 4, 29, 13, 21),
                23,
            ),
            (
                12,
                22,
                datetime(2022, 4, 29),
                "AC",
                "CA/2022/9906",
                datetime(2022, 4, 29, 13, 21),
                24,
            ),
            (
                14,
                24,
                datetime(2022, 4, 29),
                "DR",
                "CA/2022/9908",
                datetime(2022, 4, 29, 13, 21),
                25,
            ),
            (
                15,
                11,
                datetime(2022, 4, 29),
                "AR",
                "CA/2022/9909",
                datetime(2022, 4, 29, 13, 21),
                26,
            ),
            (
                15,
                12,
                datetime(2022, 4, 29),
                "AR",
                "CA/2022/9909/1",
                datetime(2022, 4, 29, 13, 21),
                27,
            ),
            (
                15,
                25,
                datetime(2022, 4, 29),
                "AC",
                "CA/2022/9909/2",
                datetime(2022, 4, 29, 13, 21),
                28,
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
                datetime.now(),  # created_datetime
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
                datetime.now(),  # created_datetime
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
                "gmp-cert-1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-3.pdf",  # path
                datetime.now(),  # created_datetime
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
                datetime.now(),  # created_datetime
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
                datetime.now(),  # created_datetime
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
                datetime.now(),  # created_datetime
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
                datetime.now(),  # created_datetime
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
                datetime.now(),  # created_datetime
                2,  # created_by_id
                32415679,  # check_code
                "CFS",  # prefix
                2022,  # year
                2,  # reference_no
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
                datetime.now(),  # sent_datetime
                datetime.now(),  # closed_datetime
                "CA_BEIS_EMAIL",  # template_code
            ),
            (
                9,  # ca_id
                "OPEN",  # status
                "a@example.com",  # to /PS-IGNORE
                "subject",  # subject
                "body",  # body
                None,  # response
                datetime.now(),  # sent_datetime
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
                datetime.now(),  # sent_datetime
                datetime.now(),  # closed_datetime
                "CA_HSE_EMAIL",  # template_code
            ),
            (
                15,  # ca_id
                "OPEN",  # status
                "a@example.com",  # to /PS-IGNORE
                "subject",  # subject
                "body",  # body
                None,  # response
                datetime.now(),  # sent_datetime
                None,  # closed_datetime
                "CA_HSE_EMAIL",  # template_code
            ),
        ],
    ),
}
