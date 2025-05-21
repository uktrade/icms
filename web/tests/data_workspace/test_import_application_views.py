from typing import Any

import pytest
from django.urls import reverse

from web.models import SILLegacyGoods

from ._base import DATE_STR_FORMAT, DT_STR_FORMAT, DT_STR_FORMAT_SECS, BaseTestDataView


class TestImportApplicationDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        cw_client,
        opt_app_submitted,
        sps_app_submitted,
        fa_dfl_app_pre_sign,
        fa_oil_app_processing,
        fa_sil_app_processing,
        fa_sil_app_submitted,
        nuclear_app_completed,
        completed_sanctions_app,
    ):
        self.client = cw_client
        self.url = reverse("data-workspace:import-application-data", kwargs={"version": "v0"})
        self.dfl = fa_dfl_app_pre_sign
        self.dfl.refresh_from_db()
        self.oil = fa_oil_app_processing
        self.oil.refresh_from_db()
        self.sil_processing = fa_sil_app_processing
        self.sil_processing.refresh_from_db()
        self.sil_submitted = fa_sil_app_submitted
        self.sil_submitted.refresh_from_db()
        self.nmil = nuclear_app_completed
        self.sanctions = completed_sanctions_app

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "agent_id": None,
                "agent_office_id": None,
                "applicant_reference": "applicant_reference value",
                "application_sub_type": "DEACTIVATED",
                "application_type_code": "FA",
                "chief_usage_status": None,
                "commodity_group_id": None,
                "consignment_country_name": "Albania",
                "contact_id": 2,
                "cover_letter_text": "Example Cover letter",
                "created": self.dfl.created.strftime(DT_STR_FORMAT),
                "created_by_id": 2,
                "decision": "APPROVE",
                "finished": None,
                "id": self.dfl.pk,
                "imi_submit_datetime": None,
                "imi_submitted_by_id": None,
                "importer_id": 1,
                "importer_office_id": 1,
                "is_active": True,
                "last_submit_datetime": "2024-01-01T12:00:00Z",
                "last_update_datetime": self.dfl.last_update_datetime.strftime(DT_STR_FORMAT),
                "last_updated_by_id": 2,
                "legacy_case_flag": False,
                "origin_country_name": "Afghanistan",
                "process_type": "DFLApplication",
                "reassign_datetime": None,
                "reference": "IMA/2024/00001",
                "refuse_reason": None,
                "status": "PROCESSING",
                "submit_datetime": "2024-01-01T12:00:00Z",
                "submitted_by_id": 2,
                "variation_decision": None,
                "variation_number": 0,
                "variation_refuse_reason": None,
            },
            {
                "agent_id": None,
                "agent_office_id": None,
                "applicant_reference": "applicant_reference value",
                "application_sub_type": "OIL",
                "application_type_code": "FA",
                "chief_usage_status": None,
                "commodity_group_id": None,
                "consignment_country_name": "Any Country",
                "contact_id": 2,
                "cover_letter_text": "Example Cover letter",
                "created": self.oil.created.strftime(DT_STR_FORMAT),
                "created_by_id": 2,
                "decision": "APPROVE",
                "finished": None,
                "id": self.oil.pk,
                "imi_submit_datetime": None,
                "imi_submitted_by_id": None,
                "importer_id": 1,
                "importer_office_id": 1,
                "is_active": True,
                "last_submit_datetime": "2024-01-01T12:00:00Z",
                "last_update_datetime": self.oil.last_update_datetime.strftime(DT_STR_FORMAT),
                "last_updated_by_id": 2,
                "legacy_case_flag": False,
                "origin_country_name": "Any Country",
                "process_type": "OpenIndividualLicenceApplication",
                "reassign_datetime": None,
                "reference": "IMA/2024/00002",
                "refuse_reason": None,
                "status": "PROCESSING",
                "submit_datetime": "2024-01-01T12:00:00Z",
                "submitted_by_id": 2,
                "variation_decision": None,
                "variation_number": 0,
                "variation_refuse_reason": None,
            },
            {
                "agent_id": None,
                "agent_office_id": None,
                "applicant_reference": "applicant_reference value",
                "application_sub_type": "SIL",
                "application_type_code": "FA",
                "chief_usage_status": None,
                "commodity_group_id": None,
                "consignment_country_name": "Afghanistan",
                "contact_id": 2,
                "cover_letter_text": "Example Cover letter",
                "created": self.sil_processing.created.strftime(DT_STR_FORMAT),  # HERE
                "created_by_id": 2,
                "decision": "APPROVE",
                "finished": None,
                "id": self.sil_processing.pk,
                "imi_submit_datetime": None,
                "imi_submitted_by_id": None,
                "importer_id": 1,
                "importer_office_id": 1,
                "is_active": True,
                "last_submit_datetime": "2024-01-01T12:00:00Z",
                "last_update_datetime": self.sil_processing.last_update_datetime.strftime(
                    DT_STR_FORMAT
                ),
                "last_updated_by_id": 2,
                "legacy_case_flag": False,
                "origin_country_name": "Afghanistan",
                "process_type": "SILApplication",
                "reassign_datetime": None,
                "reference": "IMA/2024/00003",
                "refuse_reason": None,
                "status": "PROCESSING",
                "submit_datetime": "2024-01-01T12:00:00Z",
                "submitted_by_id": 2,
                "variation_decision": None,
                "variation_number": 0,
                "variation_refuse_reason": None,
            },
            {
                "agent_id": None,
                "agent_office_id": None,
                "applicant_reference": "applicant_reference value",
                "application_sub_type": "SIL",
                "application_type_code": "FA",
                "chief_usage_status": None,
                "commodity_group_id": None,
                "consignment_country_name": "Afghanistan",
                "contact_id": 2,
                "cover_letter_text": None,
                "created": self.sil_submitted.created.strftime(DT_STR_FORMAT),
                "created_by_id": 2,
                "decision": None,
                "finished": None,
                "id": self.sil_submitted.pk,
                "imi_submit_datetime": None,
                "imi_submitted_by_id": None,
                "importer_id": 1,
                "importer_office_id": 1,
                "is_active": True,
                "last_submit_datetime": "2024-01-01T12:00:00Z",
                "last_update_datetime": self.sil_submitted.last_update_datetime.strftime(
                    DT_STR_FORMAT_SECS
                ),
                "last_updated_by_id": 2,
                "legacy_case_flag": False,
                "origin_country_name": "Afghanistan",
                "process_type": "SILApplication",
                "reassign_datetime": None,
                "reference": "IMA/2024/00004",
                "refuse_reason": None,
                "status": "SUBMITTED",
                "submit_datetime": "2024-01-01T12:00:00Z",
                "submitted_by_id": 2,
                "variation_decision": None,
                "variation_number": 0,
                "variation_refuse_reason": None,
            },
            {
                "agent_id": None,
                "agent_office_id": None,
                "applicant_reference": "applicant_reference value",
                "application_sub_type": None,
                "application_type_code": "NMIL",
                "chief_usage_status": None,
                "commodity_group_id": None,
                "consignment_country_name": "Afghanistan",
                "contact_id": 2,
                "cover_letter_text": None,
                "created": self.nmil.created.strftime(DT_STR_FORMAT),
                "created_by_id": 2,
                "decision": "APPROVE",
                "finished": None,
                "id": self.nmil.pk,
                "imi_submit_datetime": None,
                "imi_submitted_by_id": None,
                "importer_id": 1,
                "importer_office_id": 1,
                "is_active": True,
                "last_submit_datetime": "2024-01-01T12:00:00Z",
                "last_update_datetime": self.nmil.last_update_datetime.strftime(DT_STR_FORMAT),
                "last_updated_by_id": 2,
                "legacy_case_flag": False,
                "origin_country_name": "Belarus",
                "process_type": "NuclearMaterialApplication",
                "reassign_datetime": None,
                "reference": "IMA/2024/00005",
                "refuse_reason": None,
                "status": "COMPLETED",
                "submit_datetime": "2024-01-01T12:00:00Z",
                "submitted_by_id": 2,
                "variation_decision": None,
                "variation_number": 0,
                "variation_refuse_reason": None,
            },
            {
                "agent_id": None,
                "agent_office_id": None,
                "applicant_reference": "applicant_reference value",
                "application_sub_type": "ADHOC1",
                "application_type_code": "ADHOC",
                "chief_usage_status": None,
                "commodity_group_id": None,
                "consignment_country_name": "Afghanistan",
                "contact_id": 2,
                "cover_letter_text": "Example Cover letter",
                "created": self.sanctions.created.strftime(DT_STR_FORMAT),
                "created_by_id": 2,
                "decision": "APPROVE",
                "finished": None,
                "id": self.sanctions.pk,
                "imi_submit_datetime": None,
                "imi_submitted_by_id": None,
                "importer_id": 1,
                "importer_office_id": 1,
                "is_active": True,
                "last_submit_datetime": "2024-01-01T12:00:00Z",
                "last_update_datetime": self.sanctions.last_update_datetime.strftime(DT_STR_FORMAT),
                "last_updated_by_id": 2,
                "legacy_case_flag": False,
                "origin_country_name": "Belarus",
                "process_type": "SanctionsAndAdhocApplication",
                "reassign_datetime": None,
                "reference": "IMA/2024/00006",
                "refuse_reason": None,
                "status": "COMPLETED",
                "submit_datetime": "2024-01-01T12:00:00Z",
                "submitted_by_id": 2,
                "variation_decision": None,
                "variation_number": 0,
                "variation_refuse_reason": None,
            },
        ]


class TestImportLicenceDocumentDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        cw_client,
        completed_gmp_app,
        cfs_app_pre_sign,
        completed_com_app,
        opt_app_submitted,
        sps_app_submitted,
        fa_dfl_app_pre_sign,
        fa_oil_app_processing,
        fa_sil_app_processing,
        fa_sil_app_submitted,
        nuclear_app_completed,
        completed_sanctions_app,
    ):
        self.client = cw_client
        self.url = reverse("data-workspace:import-licence-document-data", kwargs={"version": "v0"})
        self.dfl = fa_dfl_app_pre_sign
        self.dfl_licence = self.dfl.licences.first()

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert len(result["results"]) == 8
        assert result["results"][0] == {
            "application_id": self.dfl.pk,
            "document_pack_id": self.dfl_licence.pk,
            "document_pack_status": "DR",
            "document_type": "COVER_LETTER",
            "id": self.dfl_licence.document_references.get(document_type="COVER_LETTER").pk,
            "issue_date": "2020-01-01T00:00:00Z",
            "reference": None,
        }
        assert result["results"][1] == {
            "application_id": self.dfl.pk,
            "document_pack_id": self.dfl_licence.pk,
            "document_pack_status": "DR",
            "document_type": "LICENCE",
            "id": self.dfl_licence.document_references.get(document_type="LICENCE").pk,
            "issue_date": "2020-01-01T00:00:00Z",
            "reference": "GBSIL0000001B",
        }


class TestFaDflApplicationDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_dfl_app):
        self.client = cw_client
        self.url = reverse("data-workspace:fa-dfl-application-data", kwargs={"version": "v0"})
        self.dfl = completed_dfl_app

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "commodity_code": "ex Chapter 93",
                "constabulary_name": "Derbyshire",
                "deactivated_firearm": True,
                "id": self.dfl.pk,
                "know_bought_from": False,
                "proof_checked": True,
            },
        ]


class TestFaDflGoodsDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_dfl_app):
        self.client = cw_client
        self.url = reverse("data-workspace:fa-dfl-goods-data", kwargs={"version": "v0"})
        self.dfl = completed_dfl_app
        self.goods = self.dfl.goods_certificates.first()

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "application_id": self.dfl.pk,
                "deactivated_certificate_reference": "deactivated_certificate_reference value",
                "goods_description": "goods_description value",
                "goods_description_original": "goods_description value",
                "id": self.goods.pk,
                "issuing_country_name": "Austria",
            }
        ]


class TestFaOilApplicationDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_oil_app):
        self.client = cw_client
        self.url = reverse("data-workspace:fa-oil-application-data", kwargs={"version": "v0"})
        self.oil = completed_oil_app

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "commodity_code": "ex Chapter 93",
                "id": self.oil.pk,
                "know_bought_from": False,
                "section1": True,
                "section2": True,
                "user_imported_certificates_count": 1,
                "verified_certificates_count": 0,
            }
        ]


class TestFaSilApplicationDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_sil_app):
        self.client = cw_client
        self.url = reverse("data-workspace:fa-sil-application-data", kwargs={"version": "v0"})
        self.sil = completed_sil_app

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "additional_comments": "",
                "commodity_code": "ex Chapter 93",
                "eu_single_market": True,
                "id": self.sil.pk,
                "know_bought_from": False,
                "manufactured": False,
                "military_police": True,
                "other_description": "other_description",
                "section1": True,
                "section2": True,
                "section5": True,
                "section58_obsolete": True,
                "section58_other": True,
                "section_legacy": False,
                "user_imported_certificates_count": 1,
                "user_section5_count": 1,
                "verified_certificates_count": 0,
                "verified_section5_count": 0,
            }
        ]


class TestFaSilGoodsSection1DataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_sil_app):
        self.client = cw_client
        self.url = reverse("data-workspace:fa-sil-goods-section1-data", kwargs={"version": "v0"})
        self.sil = completed_sil_app
        self.section1 = self.sil.goods_section1.first()

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "application_id": self.sil.pk,
                "description": "Section 1 goods",
                "description_original": "Section 1 goods",
                "id": self.section1.pk,
                "manufacture": False,
                "quantity": 111,
                "quantity_original": 111,
                "unlimited_quantity": False,
            }
        ]


class TestFaSilGoodsSection2DataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_sil_app):
        self.client = cw_client
        self.url = reverse("data-workspace:fa-sil-goods-section2-data", kwargs={"version": "v0"})
        self.sil = completed_sil_app
        self.section2 = self.sil.goods_section2.first()

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "application_id": self.sil.pk,
                "description": "Section 2 goods",
                "description_original": "Section 2 goods",
                "id": self.section2.pk,
                "manufacture": False,
                "quantity": 222,
                "quantity_original": 222,
                "unlimited_quantity": False,
            }
        ]


class TestFaSilGoodsSection5DataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_sil_app):
        self.client = cw_client
        self.url = reverse("data-workspace:fa-sil-goods-section5-data", kwargs={"version": "v0"})
        self.sil = completed_sil_app
        self.section5 = self.sil.goods_section5.get(unlimited_quantity=False)
        self.section5_uq = self.sil.goods_section5.get(unlimited_quantity=True)

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "application_id": self.sil.pk,
                "description": "Section 5 goods",
                "description_original": "Section 5 goods",
                "id": self.section5.pk,
                "manufacture": False,
                "quantity": 333,
                "quantity_original": 333,
                "section_5_clause_name": "5(A)",
                "unlimited_quantity": False,
            },
            {
                "application_id": self.sil.pk,
                "description": "Unlimited Section 5 goods",
                "description_original": "Unlimited Section 5 goods",
                "id": self.section5_uq.pk,
                "manufacture": False,
                "quantity": None,
                "quantity_original": None,
                "section_5_clause_name": "5(A)",
                "unlimited_quantity": True,
            },
        ]


class TestFaSilGoodsSectionObsoleteDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_sil_app):
        self.client = cw_client
        self.url = reverse(
            "data-workspace:fa-sil-goods-section-obsolete-data", kwargs={"version": "v0"}
        )
        self.sil = completed_sil_app
        self.section_obsolete = self.sil.goods_section582_obsoletes.first()

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "application_id": self.sil.pk,
                "acknowledgement": True,
                "centrefire": True,
                "curiosity_ornament": True,
                "description": "Section 58 obsoletes goods",
                "description_original": "Section 58 obsoletes goods",
                "id": self.section_obsolete.pk,
                "manufacture": True,
                "obsolete_calibre": ".22 Extra Long Maynard",
                "original_chambering": True,
                "quantity": 444,
                "quantity_original": 444,
            }
        ]


class TestFaSilGoodsSectionOtherDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_sil_app):
        self.client = cw_client
        self.url = reverse(
            "data-workspace:fa-sil-goods-section-other-data", kwargs={"version": "v0"}
        )
        self.sil = completed_sil_app
        self.section_other = self.sil.goods_section582_others.first()

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "application_id": self.sil.pk,
                "acknowledgement": True,
                "bore": False,
                "bore_details": "",
                "chamber": False,
                "curiosity_ornament": True,
                "description": "Section 58 other goods",
                "description_original": "Section 58 other goods",
                "id": self.section_other.pk,
                "ignition": False,
                "ignition_details": "",
                "ignition_other": "",
                "manufacture": True,
                "muzzle_loading": True,
                "quantity": 555,
                "quantity_original": 555,
                "rimfire": False,
                "rimfire_details": "",
            }
        ]


class TestFaSilGoodsSectionLegacyDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_sil_app):
        self.client = cw_client
        self.url = reverse(
            "data-workspace:fa-sil-goods-section-legacy-data", kwargs={"version": "v0"}
        )
        self.sil = completed_sil_app
        self.goods = SILLegacyGoods.objects.create(
            import_application=self.sil,
            description="Test legacy",
            description_original="Test legacy",
            quantity=100,
            quantity_original=100,
            obsolete_calibre="Test OC",
        )

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "application_id": self.sil.pk,
                "description": "Test legacy",
                "description_original": "Test legacy",
                "id": self.goods.pk,
                "obsolete_calibre": "Test OC",
                "quantity": 100,
                "quantity_original": 100,
                "unlimited_quantity": False,
            }
        ]


class TestNuclearMaterialApplicationDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, nuclear_app_completed):
        self.client = cw_client
        self.url = reverse(
            "data-workspace:nuclear-material-application-data", kwargs={"version": "v0"}
        )
        self.nmil = nuclear_app_completed

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "consignor_address": "Test consignor address",
                "consignor_name": "Test consignor name",
                "end_user_address": "Test end user address",
                "end_user_name": "Test end user name",
                "id": self.nmil.pk,
                "intended_use_of_shipment": "Test intended use of shipment",
                "licence_type": "S",
                "nature_of_business": "Test nature of business",
                "security_team_contact_information": "Test security team contact information",
                "shipment_end_date": None,
                "shipment_start_date": self.nmil.shipment_start_date.strftime(DATE_STR_FORMAT),
                "supporting_documents_count": 1,
            },
        ]


class TestNuclearMaterialGoodsDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, nuclear_app_completed):
        self.client = cw_client
        self.url = reverse("data-workspace:nuclear-material-goods-data", kwargs={"version": "v0"})
        self.nmil = nuclear_app_completed

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert len(result["results"]) == 3
        assert result["results"][0] == {
            "application_id": self.nmil.pk,
            "commodity_code": "2612101000",
            "goods_description": "Test Goods",
            "goods_description_original": "Test Goods",
            "id": self.nmil.nuclear_goods.first().pk,
            "quantity_amount": "1000.000",
            "quantity_amount_original": "1000.000",
            "unit": "Kilogramme",
            "unlimited_quantity": False,
        }


class TestSanctionsApplicationDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_sanctions_app):
        self.client = cw_client
        self.url = reverse("data-workspace:sanctions-application-data", kwargs={"version": "v0"})
        self.sanctions = completed_sanctions_app

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "exporter_address": "Test Address",
                "exporter_name": "Test Exporter",
                "id": self.sanctions.pk,
                "supporting_documents_count": 1,
            },
        ]


class TestSanctionsGoodsDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_sanctions_app):
        self.client = cw_client
        self.url = reverse("data-workspace:sanctions-goods-data", kwargs={"version": "v0"})
        self.sanctions = completed_sanctions_app

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert result["results"] == [
            {
                "application_id": self.sanctions.pk,
                "commodity_code": "4202199090",
                "goods_description": "Test Goods",
                "goods_description_original": "Test Goods",
                "id": self.sanctions.sanctions_goods.first().pk,
                "quantity_amount": "1000.000",
                "quantity_amount_original": "1000.000",
                "value": "10500.00",
                "value_original": "10500.00",
            },
            {
                "application_id": self.sanctions.pk,
                "commodity_code": "9013109000",
                "goods_description": "More Commoditites",
                "goods_description_original": "More Commoditites",
                "id": self.sanctions.sanctions_goods.last().pk,
                "quantity_amount": "56.780",
                "quantity_amount_original": "56.780",
                "value": "789.00",
                "value_original": "789.00",
            },
        ]
