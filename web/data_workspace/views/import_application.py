from typing import Any

from django.db.models import Count, F

from web.data_workspace import serializers
from web.models import SILGoodsSection582Obsolete  # /PS-IGNORE
from web.models import SILGoodsSection582Other  # /PS-IGNORE
from web.models import (
    CaseDocumentReference,
    DFLApplication,
    DFLGoodsCertificate,
    ImportApplication,
    NuclearMaterialApplication,
    NuclearMaterialApplicationGoods,
    OpenIndividualLicenceApplication,
    SanctionsAndAdhocApplication,
    SanctionsAndAdhocApplicationGoods,
    SILApplication,
    SILGoodsSection1,
    SILGoodsSection2,
    SILGoodsSection5,
    SILLegacyGoods,
)

from .base import ApplicationDataViewBase, DataViewBase


class ImportApplicationDataView(ApplicationDataViewBase):
    model = ImportApplication
    qs_serializer = serializers.ImportApplicationListSerializer
    data_serializer = serializers.ImportApplicationSerializer

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return super().get_queryset_value_kwargs() | {
            "application_type_code": F("application_type__type"),
            "application_sub_type": F("application_type__sub_type"),
            "origin_country_name": F("origin_country__name"),
            "consignment_country_name": F("consignment_country__name"),
        }


class ImportLicenceDocumentDataView(DataViewBase):
    model = CaseDocumentReference
    qs_serializer = serializers.ImportLicenceDocumentListSerializer
    data_serializer = serializers.ImportLicenceDocumentSerializer

    def get_queryset_filters(self) -> dict[str, Any]:
        return {
            "import_application_licences__import_application__application_type__is_active": True
        }

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return {
            "application_id": F("import_application_licences__import_application_id"),
            "document_pack_id": F("import_application_licences__id"),
            "document_pack_status": F("import_application_licences__status"),
            "issue_date": F("import_application_licences__case_completion_datetime"),
            "issue_paper_licence_only": F("import_application_licences__issue_paper_licence_only"),
            "licence_start_date": F("import_application_licences__licence_start_date"),
            "licence_end_date": F("import_application_licences__licence_end_date"),
        }


class FaDflApplicationDataView(DataViewBase):
    model = DFLApplication
    qs_serializer = serializers.FaDflApplicationListSerializer
    data_serializer = serializers.FaDflApplicationSerializer

    def get_queryset_filters(self) -> dict[str, Any]:
        return {"submit_datetime__isnull": False}

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return {"constabulary_name": F("constabulary__name")}


class FaDflGoodsDataView(DataViewBase):
    model = DFLGoodsCertificate
    qs_serializer = serializers.FaDflGoodsListSerializer
    data_serializer = serializers.FaDflGoodsSerializer

    def get_queryset_filters(self) -> dict[str, Any]:
        return {"dfl_application__submit_datetime__isnull": False}

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return {
            "application_id": F("dfl_application__id"),
            "issuing_country_name": F("issuing_country__name"),
        }


class FaOilApplicationDataView(DataViewBase):
    model = OpenIndividualLicenceApplication
    qs_serializer = serializers.FaOilApplicationListSerializer
    data_serializer = serializers.FaOilApplicationSerializer

    def get_queryset_filters(self) -> dict[str, Any]:
        return {"submit_datetime__isnull": False}

    def get_queryset_annotations(self) -> dict[str, Any]:
        return {
            "user_imported_certificates_count": Count("user_imported_certificates"),
            "verified_certificates_count": Count("verified_certificates"),
        }


class FaSilApplicationDataView(DataViewBase):
    model = SILApplication
    qs_serializer = serializers.FaSilApplicationListSerializer
    data_serializer = serializers.FaSilApplicationSerializer

    def get_queryset_filters(self) -> dict[str, Any]:
        return {"submit_datetime__isnull": False}

    def get_queryset_annotations(self) -> dict[str, Any]:
        return {
            "user_imported_certificates_count": Count("user_imported_certificates"),
            "user_section5_count": Count("user_section5"),
            "verified_certificates_count": Count("verified_certificates"),
            "verified_section5_count": Count("verified_section5"),
        }


class FaSilGoodsBaseView(DataViewBase):
    def get_queryset_filters(self) -> dict[str, Any]:
        return {"import_application__submit_datetime__isnull": False}

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return {"application_id": F("import_application_id")}


class FaSilGoodsSection1DataView(FaSilGoodsBaseView):
    model = SILGoodsSection1
    qs_serializer = serializers.FaSilGoodsSection1ListSerializer
    data_serializer = serializers.FaSilGoodsSection1Serializer


class FaSilGoodsSection2DataView(FaSilGoodsBaseView):
    model = SILGoodsSection2
    qs_serializer = serializers.FaSilGoodsSection2ListSerializer
    data_serializer = serializers.FaSilGoodsSection2Serializer


class FaSilGoodsSection5DataView(FaSilGoodsBaseView):
    model = SILGoodsSection5
    qs_serializer = serializers.FaSilGoodsSection5ListSerializer
    data_serializer = serializers.FaSilGoodsSection5Serializer

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return super().get_queryset_value_kwargs() | {
            "section_5_clause_name": F("section_5_clause__clause")
        }


class FaSilGoodsSectionObsoleteDataView(FaSilGoodsBaseView):
    model = SILGoodsSection582Obsolete  # /PS-IGNORE
    qs_serializer = serializers.FaSilGoodsSectionObsoleteListSerializer
    data_serializer = serializers.FaSilGoodsSectionObsoleteSerializer


class FaSilGoodsSectionOtherDataView(FaSilGoodsBaseView):
    model = SILGoodsSection582Other  # /PS-IGNORE
    qs_serializer = serializers.FaSilGoodsSectionOtherListSerializer
    data_serializer = serializers.FaSilGoodsSectionOtherSerializer


class FaSilGoodsSectionLegacyDataView(FaSilGoodsBaseView):
    model = SILLegacyGoods
    qs_serializer = serializers.FaSilGoodsSectionLegacyListSerializer
    data_serializer = serializers.FaSilGoodsSectionLegacySerializer


class SanctionsApplicationDataView(DataViewBase):
    model = SanctionsAndAdhocApplication
    qs_serializer = serializers.SanctionsApplicationListSerializer
    data_serializer = serializers.SanctionsApplicationSerializer

    def get_queryset_annotations(self) -> dict[str, Any]:
        return {"supporting_documents_count": Count("supporting_documents")}


class SanctionsGoodsDataView(DataViewBase):
    model = SanctionsAndAdhocApplicationGoods
    qs_serializer = serializers.SanctionsGoodsListSerializer
    data_serializer = serializers.SanctionsGoodsSerializer

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return {
            "application_id": F("import_application_id"),
            "commodity_code": F("commodity__commodity_code"),
        }


class NuclearMaterialApplicationDataView(DataViewBase):
    model = NuclearMaterialApplication
    qs_serializer = serializers.NuclearMaterialApplicationListSerializer
    data_serializer = serializers.NuclearMaterialApplicationSerializer

    def get_queryset_annotations(self) -> dict[str, Any]:
        return {"supporting_documents_count": Count("supporting_documents")}


class NuclearMaterialGoodsDataView(DataViewBase):
    model = NuclearMaterialApplicationGoods
    qs_serializer = serializers.NuclearMaterialGoodsListSerializer
    data_serializer = serializers.NuclearMaterialGoodsSerializer

    def get_queryset_value_kwargs(self) -> dict[str, Any]:
        return {
            "application_id": F("import_application_id"),
            "commodity_code": F("commodity__commodity_code"),
            "unit": F("quantity_unit__description"),
        }
