from datetime import datetime

from data_migration.queries import export_application, files

from . import xml_data as xd
from .ia_data import IA_FILES_COLUMNS

EA_FILES_COLUMNS = [
    ("doc_folder_id",),
    ("folder_title",),
    ("file_id",),
    ("filename",),
    ("content_type",),
    ("file_size",),
    ("path",),
    ("created_datetime",),
    ("created_by_id",),
]

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
]


ea_query_result = {
    export_application.product_legislation: (
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
    export_application.export_application_type: (
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
    files.gmp_files: (
        IA_FILES_COLUMNS,
        [
            (
                31,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
                None,  # app_model
                "ISO17021",  # target_type
                "EMPTY",  # status
                4000,  # target_id
                4000,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
            (
                32,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
                None,  # app_model
                "ISO17065",  # target_type
                "RECEIVED",  # status
                4001,  # target_id
                4001,  # fft_id
                40001,  # version_id
                datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "gmp2/ISO17065",  # path
                "ISO17065.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                32,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
                None,  # app_model
                "ISO22716",  # target_type
                "RECEIVED",  # status
                4002,  # target_id
                4002,  # fft_id
                40002,  # version_id
                datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "gmp2/ISO22716",  # path
                "ISO22716.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                32,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
                None,  # app_model
                "ISO17021",  # target_type
                "EMPTY",  # status
                4003,  # target_id
                4003,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
            (
                33,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
                None,  # app_model
                "ISO17021",  # target_type
                "RECEIVED",  # status
                4004,  # target_id
                4004,  # fft_id
                40004,  # version_id
                datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "gmp3/ISO17021",  # path
                "ISO17021.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                31,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
                None,  # app_model
                "BRCGS",  # target_type
                "RECEIVED",  # status
                4005,  # target_id
                4005,  # fft_id
                40005,  # version_id
                datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "gmp1/BRCGS",  # path
                "BRCGS.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
        ],
    ),
    export_application.gmp_application: (
        EA_BASE_COLUMNS
        + [
            ("brand_name",),
            ("file_folder_id",),
        ],
        [
            (
                7,  # ca_id
                17,  # cad_id
                "CertificateofGoodManufacturingPractice",  # process_type
                "CA/2022/9901",  # reference
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
                None,  # brand_name
                31,  # file_folder_id
            ),
            (
                8,
                18,
                "CertificateofGoodManufacturingPractice",
                "CA/2022/9902",
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
                "A brand",
                32,
            ),
            (
                9,
                19,
                "CertificateofGoodManufacturingPractice",
                "CA/2022/9903",
                "COMPLETED",
                2,
                datetime(2022, 4, 28),
                datetime(2022, 4, 28),
                datetime(2022, 4, 29),
                2,
                datetime(2022, 4, 29),
                0,
                21,
                2,
                "e-2-2",
                None,  # case_note_xml
                None,  # fir_xml
                None,  # update_request_xml
                "Another brand",
                33,
            ),
        ],
    ),
    export_application.export_application_countries: (
        [("cad_id",), ("country_id",)],
        [(18, 1), (18, 2), (18, 3), (19, 1), (21, 1), (22, 1), (24, 1), (25, 1)],
    ),
    export_application.com_application: (
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
                0,  # is_pesticide_on_free_sale_uk
                1,  # is_manufacturer
                "Another product",  # product_name
                "Another chemical",  # chemical_name
                "Test process",  # manufacturing_process
            ),
        ],
    ),
    export_application.cfs_application: (
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
            ),
            (
                14,
                24,
                "CertificateOfFreeSaleApplication",  # process_type
                "CA/2022/9908",
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
                xd.export_fir_xml_2,  # fir_xml
                None,  # update_request_xml
            ),
            (
                15,
                25,
                "CertificateOfFreeSaleApplication",  # process_type
                "CA/2022/9909",
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
                xd.export_case_note_2,  # case_note_xml
                None,  # fir_xml
                None,  # update_request_xml
            ),
        ],
    ),
    export_application.cfs_schedule: (
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
    export_application.export_certificate: (
        [
            ("ca_id",),
            ("cad_id",),
            ("case_completion_datetime",),
            ("status",),
            ("case_reference",),
            ("created_at",),
        ],
        [
            (8, 18, datetime(2022, 4, 29), "DR", "CA/2022/9902", datetime(2022, 4, 29, 13, 21)),
            (9, 10, datetime(2022, 4, 29), "AR", "CA/2022/9903", datetime(2022, 4, 29, 13, 21)),
            (9, 19, datetime(2022, 4, 29), "AC", "CA/2022/9903/1", datetime(2022, 4, 29, 13, 21)),
            (11, 21, datetime(2022, 4, 29), "DR", "CA/2022/9905", datetime(2022, 4, 29, 13, 21)),
            (12, 22, datetime(2022, 4, 29), "AC", "CA/2022/9906", datetime(2022, 4, 29, 13, 21)),
            (14, 24, datetime(2022, 4, 29), "DR", "CA/2022/9908", datetime(2022, 4, 29, 13, 21)),
            (15, 11, datetime(2022, 4, 29), "AR", "CA/2022/9909", datetime(2022, 4, 29, 13, 21)),
            (15, 12, datetime(2022, 4, 29), "AR", "CA/2022/9909/1", datetime(2022, 4, 29, 13, 21)),
            (15, 25, datetime(2022, 4, 29), "AC", "CA/2022/9909/2", datetime(2022, 4, 29, 13, 21)),
        ],
    ),
    export_application.export_certificate_docs: (
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
        ],
        [
            (
                18,  # cad_id
                1,  # certificate_id
                101,  # document_legacy_id
                "GMP/2022/00001",  # reference
                "GMP/2022/00001",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                1,  # country_id
                "gmp-cert-1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-1.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                18,  # cad_id
                2,  # certificate_id
                102,  # document_legacy_id
                "GMP/2022/00002",  # reference
                "GMP/2022/00002",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                2,  # country_id
                "gmp-cert-2.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-2.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                18,  # cad_id
                3,  # certificate_id
                103,  # document_legacy_id
                "GMP/2022/00003",  # reference
                "GMP/2022/00003",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                3,  # country_id
                "gmp-cert-1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-3.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                19,  # cad_id
                4,  # certificate_id
                104,  # document_legacy_id
                "GMP/2022/00004",  # reference
                "GMP/2022/00004",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                1,  # country_id
                "gmp-cert-4.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-4.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                21,  # cad_id
                5,  # certificate_id
                105,  # document_legacy_id
                "COM/2022/00001",  # reference
                "COM/2022/00001",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                1,  # country_id
                "com-cert-1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/com-cert-1.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                22,  # cad_id
                6,  # certificate_id
                106,  # document_legacy_id
                "COM/2022/00002",  # reference
                "COM/2022/00002",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                1,  # country_id
                "com-cert-2.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/com-cert-2.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                24,  # cad_id
                7,  # certificate_id
                107,  # document_legacy_id
                "CFS/2022/00001",  # reference
                "CFS/2022/00001",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                1,  # country_id
                "cfs-cert-1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/cfs-cert-1.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                25,  # cad_id
                8,  # certificate_id
                108,  # document_legacy_id
                "CFS/2022/00002",  # reference
                "CFS/2022/00002",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                1,  # country_id
                "cfs-cert-2.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/cfs-cert-2.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
        ],
    ),
    export_application.export_variations: (
        [
            ("ca_id",),
            ("is_active",),
            ("case_reference",),
            ("status",),
            ("requested_datetime",),
            ("requested_by_id",),
            ("what_varied",),
            ("closed_datetime",),
            ("closed_by_id",),
        ],
        [
            (
                9,  # ca_id
                0,  # is_active
                "CA/2022/9903/1",  # case_reference
                "CLOSED",  # status
                datetime.now(),  # requested_datetime
                2,  # requested_by_id
                "Make changes",  # what_varied
                datetime.now(),  # closed_datetime
                2,  # closed_by_id
            ),
            (
                15,  # ca_id
                0,  # is_active
                "CA/2022/9909/1",  # case_reference
                "CLOSED",  # status
                datetime.now(),  # requested_datetime
                2,  # requested_by_id
                "First changes",  # what_varied
                datetime.now(),  # closed_datetime
                2,  # closed_by_id
            ),
            (
                15,  # ca_id
                1,  # is_active
                "CA/2022/9909/2",  # case_reference
                "OPEN",  # status
                datetime.now(),  # requested_datetime
                2,  # requested_by_id
                "Second changes",  # what_varied
                datetime.now(),  # closed_datetime
                2,  # closed_by_id
            ),
        ],
    ),
    files.export_case_note_docs: (
        EA_FILES_COLUMNS,
        [
            (
                1,  # doc_folder_id
                "Case Note 1",  # folder_title
                1,  # file_id
                "Case Note File.pdf",  # filename
                "pdf",  # content_type
                1000,  # file_size
                "1-Case Note File.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                2,  # doc_folder_id
                "Case Note 1",  # folder_title
                None,  # file_id
                None,  # filename
                None,  # content_type
                None,  # file_size
                None,  # path
                None,  # created_datetime
                None,  # created_by_id
            ),
            (
                3,  # doc_folder_id
                "Case Note 2",  # folder_title
                2,  # file_id
                "Case Note 2 File 1.pdf",  # filename
                "pdf",  # content_type
                1000,  # file_size
                "2-Case Note File.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                3,  # doc_folder_id
                "Case Note 2",  # folder_title
                3,  # file_id
                "Case Note 2 File 2.pdf",  # filename
                "pdf",  # content_type
                1000,  # file_size
                "3-Case Note File.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                4,  # doc_folder_id
                "Case Note 2",  # folder_title
                None,  # file_id
                None,  # filename
                None,  # content_type
                None,  # file_size
                None,  # path
                None,  # created_datetime
                None,  # created_by_id
            ),
        ],
    ),
    export_application.beis_emails: (
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
                9,  # ca_id
                "CLOSED",  # status
                "a@example.com",  # to /PS-IGNORE
                "subject",  # subject
                "body",  # body
                "response",  # response
                datetime.now(),  # sent_datetime
                datetime.now(),  # closed_datetime
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
            ),
        ],
    ),
    export_application.hse_emails: (
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
            ),
        ],
    ),
}
