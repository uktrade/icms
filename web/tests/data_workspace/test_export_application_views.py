from typing import Any

import pytest
from django.urls import reverse

from ._base import DT_STR_FORMAT, DT_STR_FORMAT_SECS, BaseTestDataView


class TestExportApplicationDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, cfs_app_processing, completed_gmp_app, com_app_submitted):
        self.client = cw_client
        self.url = reverse("data-workspace:export-application-data", kwargs={"version": "v0"})
        self.cfs = cfs_app_processing
        self.gmp = completed_gmp_app
        self.com = com_app_submitted

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "id": self.cfs.pk,
                "process_type": "CertificateOfFreeSaleApplication",
                "is_active": True,
                "created": self.cfs.created.strftime(DT_STR_FORMAT),
                "finished": None,
                "status": "PROCESSING",
                "submit_datetime": "2024-01-01T12:00:00Z",
                "last_submit_datetime": "2024-01-01T12:00:00Z",
                "reassign_datetime": None,
                "reference": "CA/2024/00001",
                "decision": "APPROVE",
                "refuse_reason": None,
                "agent_id": None,
                "agent_office_id": None,
                "last_update_datetime": self.cfs.last_update_datetime.strftime(DT_STR_FORMAT),
                "last_updated_by_id": 8,
                "variation_number": 0,
                "created_by_id": 8,
                "submitted_by_id": 8,
                "country_names": ["Afghanistan", "Zimbabwe"],
                "applicant_reference": "",
                "application_type_code": "CFS",
                "exporter_id": 1,
                "exporter_office_id": 6,
                "contact_id": 8,
            },
            {
                "id": self.gmp.pk,
                "process_type": "CertificateofGoodManufacturingPractice",
                "is_active": True,
                "created": self.gmp.created.strftime(DT_STR_FORMAT),
                "finished": None,
                "status": "COMPLETED",
                "submit_datetime": "2024-01-01T12:00:00Z",
                "last_submit_datetime": "2024-01-01T12:00:00Z",
                "reassign_datetime": None,
                "reference": "GA/2024/00001",
                "decision": "APPROVE",
                "refuse_reason": None,
                "agent_id": None,
                "agent_office_id": None,
                "last_update_datetime": self.gmp.last_update_datetime.strftime(DT_STR_FORMAT),
                "last_updated_by_id": 8,
                "variation_number": 0,
                "created_by_id": 8,
                "submitted_by_id": 8,
                "country_names": ["China"],
                "applicant_reference": "",
                "application_type_code": "GMP",
                "exporter_id": 1,
                "exporter_office_id": 6,
                "contact_id": 8,
            },
            {
                "id": self.com.pk,
                "process_type": "CertificateOfManufactureApplication",
                "is_active": True,
                "created": self.com.created.strftime(DT_STR_FORMAT),
                "finished": None,
                "status": "SUBMITTED",
                "submit_datetime": "2024-01-01T12:00:00Z",
                "last_submit_datetime": "2024-01-01T12:00:00Z",
                "reassign_datetime": None,
                "reference": "CA/2024/00002",
                "decision": None,
                "refuse_reason": None,
                "agent_id": None,
                "agent_office_id": None,
                "last_update_datetime": self.com.last_update_datetime.strftime(DT_STR_FORMAT_SECS),
                "last_updated_by_id": 8,
                "variation_number": 0,
                "created_by_id": 8,
                "submitted_by_id": 8,
                "country_names": ["Afghanistan"],
                "applicant_reference": "",
                "application_type_code": "COM",
                "exporter_id": 1,
                "exporter_office_id": 6,
                "contact_id": 8,
            },
        ]


class TestGMPApplicationDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_gmp_app):
        self.client = cw_client
        self.url = reverse("data-workspace:gmp-application-data", kwargs={"version": "v0"})
        self.gmp = completed_gmp_app

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "id": self.gmp.pk,
                "brand_name": "A Brand",
                "is_responsible_person": "yes",
                "responsible_person_name": "RP Name",
                "responsible_person_address_entry_type": "SEARCH",
                "responsible_person_postcode": "RP Postcode",
                "responsible_person_address": "RP Address",
                "responsible_person_country": "GB",
                "is_manufacturer": "yes",
                "manufacturer_name": "MAN Name",
                "manufacturer_address_entry_type": "SEARCH",
                "manufacturer_postcode": "MAN Postcode",
                "manufacturer_address": "MAN Address",
                "manufacturer_country": "GB",
                "gmp_certificate_issued": "ISO_22716",
                "auditor_accredited": "yes",
                "auditor_certified": "yes",
                "supporting_documents_types": ["ISO_17021", "ISO_17065", "ISO_22716"],
            }
        ]


class TestCOMApplicationDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, com_app_submitted, com_agent_app_submitted):
        self.client = cw_client
        self.url = reverse("data-workspace:com-application-data", kwargs={"version": "v0"})
        self.com = com_app_submitted
        self.com_agent = com_agent_app_submitted

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "id": self.com.pk,
                "is_pesticide_on_free_sale_uk": False,
                "is_manufacturer": True,
                "product_name": "Example product name",
                "chemical_name": "Example chemical name",
                "manufacturing_process": "Example manufacturing process",
            },
            {
                "id": self.com_agent.pk,
                "is_pesticide_on_free_sale_uk": False,
                "is_manufacturer": True,
                "product_name": "Example product name",
                "chemical_name": "Example chemical name",
                "manufacturing_process": "Example manufacturing process",
            },
        ]


class TestCFSSchedulenDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, cfs_app_processing):
        self.client = cw_client
        self.url = reverse("data-workspace:cfs-schedule-data", kwargs={"version": "v0"})
        self.cfs = cfs_app_processing
        self.schedule = self.cfs.schedules.first()

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "id": self.schedule.pk,
                "export_application_id": self.cfs.pk,
                "exporter_status": "MANUFACTURER",
                "brand_name_holder": "yes",
                "legislation_ids": [241],
                "biocidal_claim": None,
                "product_eligibility": "MEET_UK_PRODUCT_SAFETY",
                "goods_placed_on_uk_market": "no",
                "goods_export_only": "yes",
                "product_standard": "",
                "any_raw_materials": "no",
                "final_product_end_use": "",
                "country_of_manufacture_name": "Afghanistan",
                "schedule_statements_accordance_with_standards": True,
                "schedule_statements_is_responsible_person": True,
                "manufacturer_name": None,
                "manufacturer_address_entry_type": "SEARCH",
                "manufacturer_postcode": None,
                "manufacturer_address": None,
                "created_at": self.schedule.created_at.strftime(DT_STR_FORMAT),
                "updated_at": self.schedule.updated_at.strftime(DT_STR_FORMAT),
                "is_biocidal": True,
                "is_biocidal_claim": False,
            }
        ]


class TestCFSProductDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, cfs_app_processing):
        self.client = cw_client
        self.url = reverse("data-workspace:cfs-product-data", kwargs={"version": "v0"})
        self.schedule = cfs_app_processing.schedules.first()
        self.product = self.schedule.products.first()

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "id": self.product.pk,
                "schedule_id": self.schedule.pk,
                "product_name": "A Product",
                "is_raw_material": False,
                "product_end_use": "",
                "product_type_number_list": [1],
                "active_ingredient_list": ["An Ingredient"],
                "cas_number_list": ["107-07-3"],
            }
        ]


class TestLegislationDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client):
        self.client = cw_client
        self.url = reverse("data-workspace:legislation-data", kwargs={"version": "v0"})

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert len(result["results"]) == 95
        assert result["results"][-1] == {
            "gb_legislation": True,
            "id": 364,
            "is_active": True,
            "is_biocidal": False,
            "is_biocidal_claim": True,
            "is_eu_cosmetics_regulation": False,
            "name": "Dummy 'Is Biocidal Claim legislation'",
            "ni_legislation": True,
        }


class TestExportCertificateDocumentDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        cw_client,
        completed_gmp_app,
        cfs_app_pre_sign,
        completed_com_app,
        opt_app_submitted,
        fa_dfl_app_pre_sign,
    ):
        self.client = cw_client
        self.url = reverse(
            "data-workspace:export-certificate-document-data", kwargs={"version": "v0"}
        )
        self.gmp = completed_gmp_app
        self.gmp.refresh_from_db
        self.gmp_cert = self.gmp.certificates.first()
        self.com = completed_com_app
        self.com_cert = self.com.certificates.first()
        self.cfs = cfs_app_pre_sign
        self.cfs_cert = self.cfs.certificates.first()

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert len(result["results"]) == 4
        assert result["results"] == [
            {
                "id": self.gmp_cert.document_references.first().pk,
                "application_id": self.gmp.pk,
                "document_pack_id": self.gmp_cert.pk,
                "document_pack_status": "AC",
                "issue_date": self.gmp_cert.case_completion_datetime.strftime(DT_STR_FORMAT),
                "country": "China",
                "document_type": "CERTIFICATE",
                "reference": "GMP/2025/00001",
            },
            {
                "id": self.cfs_cert.document_references.first().pk,
                "application_id": self.cfs.pk,
                "document_pack_id": self.cfs_cert.pk,
                "country": "Afghanistan",
                "document_type": "CERTIFICATE",
                "issue_date": None,
                "reference": "CFS/2025/00001",
                "document_pack_status": "DR",
            },
            {
                "id": self.cfs_cert.document_references.last().pk,
                "application_id": self.cfs.pk,
                "document_pack_id": self.cfs_cert.pk,
                "country": "Zimbabwe",
                "document_type": "CERTIFICATE",
                "issue_date": None,
                "reference": "CFS/2025/00002",
                "document_pack_status": "DR",
            },
            {
                "id": self.com_cert.document_references.first().pk,
                "application_id": self.com.pk,
                "document_pack_id": self.com_cert.pk,
                "country": "Afghanistan",
                "document_type": "CERTIFICATE",
                "issue_date": self.com_cert.case_completion_datetime.strftime(DT_STR_FORMAT),
                "reference": "COM/2025/00001",
                "document_pack_status": "AC",
            },
        ]
