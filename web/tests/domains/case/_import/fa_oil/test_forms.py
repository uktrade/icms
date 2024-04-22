import pytest

from web.domains.case._import.fa.forms import UserImportCertificateForm
from web.domains.case._import.fa.models import UserImportCertificate
from web.domains.case._import.fa_oil.forms import EditFaOILForm
from web.models import Country
from web.models.shared import FirearmCommodity
from web.tests.auth import AuthTestCase


class TestOILForm(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, fa_oil_app_in_progress):
        self.process = fa_oil_app_in_progress
        self.all_countries_object = Country.objects.get(name="Any Country")

    def get_form(self, extra_data=None):
        data = {
            "contact": self.importer_user,
            "origin_country": self.all_countries_object,
            "consignment_country": self.all_countries_object,
            "exporter_name": None,
            "exporter_address": None,
            "commodity_code": FirearmCommodity.EX_CHAPTER_93,
        }
        if extra_data:
            data.update(extra_data)

        return EditFaOILForm(data, instance=self.process, initial={"contact": self.importer_user})

    def test_form_valid(self):
        form = self.get_form()
        assert form.is_valid()

    def test_form_country_disabled(self):
        """Tests that the origin_country and consignment_country fields are disabled."""
        form = self.get_form()
        assert form.fields["origin_country"].disabled
        assert form.fields["consignment_country"].disabled

    def test_form_country_cleaned(self):
        """Tests that the origin_country and consignment_country fields are cleaned and return the correct object."""
        form = self.get_form()
        assert form.is_valid()
        assert form.cleaned_data["origin_country"] == self.all_countries_object
        assert form.cleaned_data["consignment_country"] == self.all_countries_object

    def test_form_country_queryset(self):
        """Tests that the origin_country and consignment_country fields have the correct queryset."""
        form = self.get_form()
        assert form.fields["origin_country"].queryset.count() == 1
        assert form.fields["origin_country"].queryset.get() == self.all_countries_object

        assert form.fields["consignment_country"].queryset.count() == 1
        assert form.fields["consignment_country"].queryset.get() == self.all_countries_object


def test_user_import_certificate_form(fa_oil_app_in_progress):
    form = UserImportCertificateForm(application=fa_oil_app_in_progress)
    assert len(form.fields["certificate_type"].choices) == 1
    assert (
        form.fields["certificate_type"].initial
        == UserImportCertificate.CertificateType.registered.value
    )
    assert form.fields["certificate_type"].disabled
