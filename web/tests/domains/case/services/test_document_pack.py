import datetime as dt
import re
from itertools import product

import pytest

from web.domains.case.services import document_pack
from web.models import (
    CaseDocumentReference,
    Country,
    DocumentPackBase,
    ImportApplicationType,
)

PackStatus = DocumentPackBase.Status
DocumentType = CaseDocumentReference.Type


class TestPackServiceFunctions:
    """Tests all pack_* service functions"""

    def test_pack_draft_create(self, fa_sil, com):
        licence = document_pack.pack_draft_create(fa_sil)

        assert licence.status == PackStatus.DRAFT
        # This app type allows both so doesn't default to True or False
        assert licence.issue_paper_licence_only is None

        certificate = document_pack.pack_draft_create(com)
        assert certificate.status == PackStatus.DRAFT

    def test_pack_draft_create_for_variation_request(self, fa_sil):
        licence = document_pack.pack_draft_create(fa_sil)

        licence.licence_start_date = dt.date(2022, 1, 31)
        licence.licence_end_date = dt.date(2022, 12, 31)
        licence.save()

        document_pack.pack_draft_set_active(fa_sil)

        licence_2 = document_pack.pack_draft_create(fa_sil, variation_request=True)
        assert licence_2.status == PackStatus.DRAFT

        # The new licence should get the old values
        assert licence_2.issue_paper_licence_only == licence.issue_paper_licence_only
        assert licence_2.licence_start_date == licence.licence_start_date
        assert licence_2.licence_end_date == licence.licence_end_date

    def test__get_paper_licence_only(self):
        """Private method but testing it directly is the easiest way to test the logic"""
        app_t = ImportApplicationType(electronic_licence_flag=True, paper_licence_flag=True)
        plo = document_pack._get_paper_licence_only(app_t)
        assert plo is None

        app_t.electronic_licence_flag = True
        app_t.paper_licence_flag = False
        plo = document_pack._get_paper_licence_only(app_t)
        assert plo is False

        app_t.paper_licence_flag = True
        app_t.electronic_licence_flag = False
        plo = document_pack._get_paper_licence_only(app_t)
        assert plo is True

    def test_pack_draft_get(self, fa_sil):
        document_pack.pack_draft_create(fa_sil)
        fa_sil.refresh_from_db()

        licence = document_pack.pack_draft_get(fa_sil)
        assert licence.status == PackStatus.DRAFT

    def test_pack_draft_set_active(self, fa_sil):
        initial_licence = document_pack.pack_draft_create(fa_sil)
        fa_sil.refresh_from_db()

        document_pack.pack_draft_set_active(fa_sil)

        initial_licence.refresh_from_db()
        assert initial_licence.status == PackStatus.ACTIVE
        assert initial_licence.case_reference == fa_sil.reference

        fa_sil.refresh_from_db()
        new_draft_licence = document_pack.pack_draft_create(fa_sil)
        # Fake a variation request for the case
        fa_sil.reference = f"{fa_sil.reference}/1"
        fa_sil.save()

        document_pack.pack_draft_set_active(fa_sil)

        initial_licence.refresh_from_db()
        new_draft_licence.refresh_from_db()

        assert initial_licence.status == PackStatus.ARCHIVED
        assert new_draft_licence.status == PackStatus.ACTIVE

        # Test the second licence has the updated case reference
        assert new_draft_licence.case_reference == fa_sil.reference

    def test_pack_draft_archive(self, fa_sil):
        draft_licence = document_pack.pack_draft_create(fa_sil)

        document_pack.pack_draft_archive(fa_sil)

        draft_licence.refresh_from_db()
        assert draft_licence.status == PackStatus.ARCHIVED

    def test_pack_active_get(self, fa_sil):
        draft_licence = document_pack.pack_draft_create(fa_sil)
        document_pack.pack_draft_set_active(fa_sil)

        active_licence = document_pack.pack_active_get(fa_sil)

        assert draft_licence.pk == active_licence.pk

    def test_pack_active_get_optional(self, fa_sil):
        # No licences created yet
        assert document_pack.pack_active_get_optional(fa_sil) is None

        # Create an active licence
        draft_licence = document_pack.pack_draft_create(fa_sil)
        document_pack.pack_draft_set_active(fa_sil)

        active_licence = document_pack.pack_active_get_optional(fa_sil)

        assert draft_licence.pk == active_licence.pk

    def test_pack_active_revoke(self, fa_sil):
        licence = document_pack.pack_draft_create(fa_sil)
        document_pack.pack_draft_set_active(fa_sil)

        licence.refresh_from_db()
        assert licence.status == PackStatus.ACTIVE

        revoke_reason = "Test revoke reason"
        document_pack.pack_active_revoke(fa_sil, revoke_reason, True)

        licence.refresh_from_db()
        assert licence.status == PackStatus.REVOKED
        assert licence.revoke_reason == revoke_reason
        assert licence.revoke_email_sent is True

    def test_pack_revoked_get(self, fa_sil):
        draft_licence = document_pack.pack_draft_create(fa_sil)
        document_pack.pack_draft_set_active(fa_sil)

        revoke_reason = "Test revoke reason"
        document_pack.pack_active_revoke(fa_sil, "Test revoke reason", False)

        revoked_licence = document_pack.pack_revoked_get(fa_sil)

        assert revoked_licence.pk == draft_licence.pk
        assert revoked_licence.revoke_reason == revoke_reason
        assert revoked_licence.revoke_email_sent is False

    def test_pack_latest_get(self, fa_sil):
        draft_licence = document_pack.pack_draft_create(fa_sil)

        latest_licence = document_pack.pack_latest_get(fa_sil)

        assert draft_licence.pk == latest_licence.pk
        document_pack.pack_draft_set_active(fa_sil)

        licence_2 = document_pack.pack_draft_create(fa_sil)
        latest_licence = document_pack.pack_latest_get(fa_sil)

        assert licence_2.pk == latest_licence.pk

    def test_pack_issued_get_all(self, fa_sil):
        licence_1 = document_pack.pack_draft_create(fa_sil)
        document_pack.pack_draft_set_active(fa_sil)
        licence_2 = document_pack.pack_draft_create(fa_sil)

        # Fake a variation request for the case (licences can't have duplicate references)
        fa_sil.reference = f"{fa_sil.reference}/1"
        fa_sil.save()
        document_pack.pack_draft_set_active(fa_sil)
        document_pack.pack_draft_create(fa_sil)

        issued_packs = document_pack.pack_issued_get_all(fa_sil)

        assert issued_packs.count() == 2
        # licence_1 is archived so should return
        issued_packs.get(id=licence_1.pk)
        # licence_2 is active so should return
        issued_packs.get(id=licence_2.pk)

    def test_pack_workbasket_get_issued(self, fa_sil):
        licence_1 = document_pack.pack_draft_create(fa_sil)
        document_pack.pack_draft_set_active(fa_sil)
        licence_2 = document_pack.pack_draft_create(fa_sil)

        # Fake a variation request for the case (licences can't have duplicate references)
        fa_sil.reference = f"{fa_sil.reference}/1"
        fa_sil.save()
        document_pack.pack_draft_set_active(fa_sil)
        document_pack.pack_draft_create(fa_sil)

        issued_packs = document_pack.pack_workbasket_get_issued(fa_sil)

        assert issued_packs.count() == 2
        issued_packs.get(id=licence_1.pk)
        issued_packs.get(id=licence_2.pk)

        licence_1.show_in_workbasket = False
        licence_1.save()

        issued_packs = document_pack.pack_workbasket_get_issued(fa_sil)

        assert issued_packs.count() == 1
        issued_packs.get(id=licence_2.pk)

    def test_pack_workbasket_remove_pack(self, fa_sil):
        licence_1 = document_pack.pack_draft_create(fa_sil)
        document_pack.pack_draft_set_active(fa_sil)

        issued_packs = document_pack.pack_workbasket_get_issued(fa_sil)
        assert issued_packs.count() == 1

        document_pack.pack_workbasket_remove_pack(fa_sil, pack_pk=licence_1.pk)

        issued_packs = document_pack.pack_workbasket_get_issued(fa_sil)
        assert issued_packs.count() == 0

    def test_pack_licence_history(self, fa_sil):
        licence_1 = document_pack.pack_draft_create(fa_sil)
        document_pack.pack_draft_set_active(fa_sil)
        licence_2 = document_pack.pack_draft_create(fa_sil)

        # Fake a variation request for the case (licences can't have duplicate references)
        fa_sil.reference = f"{fa_sil.reference}/1"
        fa_sil.save()
        document_pack.pack_draft_set_active(fa_sil)
        document_pack.pack_draft_create(fa_sil)

        issued_packs = document_pack.pack_licence_history(fa_sil)

        assert issued_packs.count() == 2
        # licence_1 is archived so should return
        issued_packs.get(id=licence_1.pk)
        # licence_2 is active so should return
        issued_packs.get(id=licence_2.pk)

    def test_pack_certificate_history(self, com):
        certificate_1 = document_pack.pack_draft_create(com)
        document_pack.pack_draft_set_active(com)
        certificate_2 = document_pack.pack_draft_create(com)

        # Fake a variation request for the case (licences can't have duplicate references)
        com.reference = f"{com.reference}/1"
        com.save()
        document_pack.pack_draft_set_active(com)
        document_pack.pack_draft_create(com)

        issued_packs = document_pack.pack_certificate_history(com)

        assert issued_packs.count() == 2
        # licence_1 is archived so should return
        issued_packs.get(id=certificate_1.pk)
        # licence_2 is active so should return
        issued_packs.get(id=certificate_2.pk)


class TestDocRefServiceFunctions:
    """Test all doc_ref_* service functions"""

    @pytest.fixture(autouse=True)
    def _setup(self, lock_manager):
        self.lm = lock_manager

    def test_doc_ref_documents_create_import_application(self, fa_sil_with_draft):
        document_pack.doc_ref_documents_create(fa_sil_with_draft, self.lm)

        pack = document_pack.pack_draft_get(fa_sil_with_draft)

        # A cover letter & licence should have been created
        cover_letter = document_pack.doc_ref_cover_letter_get(pack)
        assert cover_letter.document_type == DocumentType.COVER_LETTER

        licence_doc = document_pack.doc_ref_licence_get(pack)
        assert licence_doc.document_type == DocumentType.LICENCE

        # Calling this again shouldn't create anything new
        document_pack.doc_ref_documents_create(fa_sil_with_draft, self.lm)
        cover_letter_2 = document_pack.doc_ref_cover_letter_get(pack)
        assert cover_letter == cover_letter_2

        licence_doc_2 = document_pack.doc_ref_licence_get(pack)
        assert licence_doc == licence_doc_2

    def test_doc_ref_documents_create_import_application_no_cover_letter(
        self, sanctions_with_draft
    ):
        document_pack.doc_ref_documents_create(sanctions_with_draft, self.lm)

        pack = document_pack.pack_draft_get(sanctions_with_draft)

        # Only licence should have been created
        licence_doc = document_pack.doc_ref_licence_get(pack)
        assert licence_doc.document_type == DocumentType.LICENCE
        assert document_pack.doc_ref_documents_all(pack).count() == 1

        # Calling this again shouldn't create anything new
        document_pack.doc_ref_documents_create(sanctions_with_draft, self.lm)

        licence_doc_2 = document_pack.doc_ref_licence_get(pack)
        assert licence_doc == licence_doc_2
        assert document_pack.doc_ref_documents_all(pack).count() == 1

    def test_doc_ref_documents_create_export_com_application(self, com_with_draft):
        document_pack.doc_ref_documents_create(com_with_draft, self.lm)

        pack = document_pack.pack_draft_get(com_with_draft)

        # A certificate should exist for each country linked to the application
        for c in com_with_draft.countries.all():
            certificate = document_pack.doc_ref_certificate_get(pack, country=c)

            assert certificate.document_type == DocumentType.CERTIFICATE

    def test_doc_ref_documents_create_export_gmp_application(self, gmp_with_draft):
        document_pack.doc_ref_documents_create(gmp_with_draft, self.lm)

        pack = document_pack.pack_draft_get(gmp_with_draft)

        countries = gmp_with_draft.countries.order_by("name")
        brands = gmp_with_draft.brands.order_by("brand_name")

        # A certificate should exist for each country/brand combo linked to the application
        for c, b in product(countries, brands):
            certificate = document_pack.doc_ref_certificate_get(pack, country=c, brand=b)

            assert certificate.document_type == DocumentType.CERTIFICATE

    def test_doc_ref_certificate_create(self, com_with_draft):
        pack = document_pack.pack_draft_get(com_with_draft)
        country = Country.objects.first()

        with pytest.raises(
            ValueError, match="Unable to create a certificate without a document reference"
        ):
            document_pack.doc_ref_certificate_create(pack, "", country=country)

        certificate = document_pack.doc_ref_certificate_create(
            pack, "export-cert-ref", country=country
        )

        assert certificate.document_type == DocumentType.CERTIFICATE
        assert certificate.reference == "export-cert-ref"
        assert certificate.reference_data.country == country

    def test_doc_ref_certificate_get(self, com_with_draft):
        cert_ref_pattern = re.compile(
            r"""
                COM     # Prefix
                /       # Separator
                \d+     # Year
                /       # Separator
                \d+     # reference
            """,
            flags=re.IGNORECASE | re.VERBOSE,
        )

        document_pack.doc_ref_documents_create(com_with_draft, self.lm)

        pack = document_pack.pack_draft_get(com_with_draft)
        country = Country.objects.get(name="Finland")

        certificate = document_pack.doc_ref_certificate_get(pack, country)
        assert certificate.document_type == DocumentType.CERTIFICATE
        assert certificate.reference_data.country == country
        assert re.match(cert_ref_pattern, certificate.reference) is not None
        assert certificate.reference_data.gmp_brand is None

    def test_doc_ref_certificates_all(self, gmp_with_draft, com_with_draft):
        # Test GMP certificate count
        document_pack.doc_ref_documents_create(gmp_with_draft, self.lm)

        pack = document_pack.pack_draft_get(gmp_with_draft)
        country_count = gmp_with_draft.countries.count()
        brand_count = gmp_with_draft.brands.count()

        certificates = document_pack.doc_ref_certificates_all(pack)

        assert certificates.count() == country_count * brand_count

        # Test COM certificate count
        document_pack.doc_ref_documents_create(com_with_draft, self.lm)

        pack = document_pack.pack_draft_get(com_with_draft)
        country_count = gmp_with_draft.countries.count()

        certificates = document_pack.doc_ref_certificates_all(pack)

        assert certificates.count() == country_count

    def test_doc_ref_licence_create(self, fa_sil_with_draft):
        pack = document_pack.pack_draft_get(fa_sil_with_draft)

        with pytest.raises(
            ValueError, match="Unable to create a licence without a document reference"
        ):
            document_pack.doc_ref_licence_create(pack, "")

        licence = document_pack.doc_ref_licence_create(pack, "import-lic-ref")

        assert licence.document_type == DocumentType.LICENCE
        assert licence.reference == "import-lic-ref"

    def test_doc_ref_licence_get(self, fa_sil_with_draft):
        document_pack.doc_ref_documents_create(fa_sil_with_draft, self.lm)
        pack = document_pack.pack_draft_get(fa_sil_with_draft)

        licence = document_pack.doc_ref_licence_get(pack)

        assert licence.reference == "GBSIL0000001B"
        assert licence.document_type == DocumentType.LICENCE

    def test_doc_ref_licence_get_optional(self, fa_sil_with_draft):
        document_pack.doc_ref_documents_create(fa_sil_with_draft, self.lm)
        pack = document_pack.pack_draft_get(fa_sil_with_draft)

        licence = document_pack.doc_ref_licence_get_optional(pack)

        assert licence.reference == "GBSIL0000001B"
        assert licence.document_type == DocumentType.LICENCE

        licence.delete()
        assert document_pack.doc_ref_licence_get_optional(pack) is None

    def test_doc_ref_cover_letter_get(self, fa_sil_with_draft):
        document_pack.doc_ref_documents_create(fa_sil_with_draft, self.lm)
        pack = document_pack.pack_draft_get(fa_sil_with_draft)

        cover_letter = document_pack.doc_ref_cover_letter_get(pack)
        assert cover_letter.document_type == DocumentType.COVER_LETTER

        # Cover letters don't have licence / certificate references
        assert cover_letter.reference is None

    def test_doc_ref_documents_all(self, fa_sil_with_draft, gmp_with_draft, com_with_draft):
        document_pack.doc_ref_documents_create(fa_sil_with_draft, self.lm)
        pack = document_pack.pack_draft_get(fa_sil_with_draft)

        pack_documents = document_pack.doc_ref_documents_all(pack)
        # Cover letter and a licence
        assert pack_documents.count() == 2

        document_pack.doc_ref_documents_create(gmp_with_draft, self.lm)
        pack = document_pack.pack_draft_get(gmp_with_draft)

        pack_documents = document_pack.doc_ref_documents_all(pack)
        # Certificate document for each country and brand combination e.g.
        # (Finland and Germany) * (Brand 1, Brand 2, Brand 3)
        assert pack_documents.count() == 6

        document_pack.doc_ref_documents_create(com_with_draft, self.lm)
        pack = document_pack.pack_draft_get(com_with_draft)

        pack_documents = document_pack.doc_ref_documents_all(pack)
        # Certificate document for each country
        # (Finland and Germany)
        assert pack_documents.count() == 2
