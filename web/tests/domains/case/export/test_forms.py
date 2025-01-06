import pytest
from django.forms import model_to_dict
from django.template.loader import render_to_string
from django.test import TestCase

from web.domains.case.export.forms import (
    CFSActiveIngredientForm,
    CFSManufacturerDetailsForm,
    EditCFSScheduleForm,
    EditCOMForm,
    EditGMPForm,
    SubmitCFSForm,
    SubmitCFSScheduleForm,
    SubmitGMPForm,
)
from web.forms.widgets import RadioSelectInline
from web.models import Country, ProductLegislation
from web.models.shared import AddressEntryType, YesNoChoices


class TestGMPForms(TestCase):
    @pytest.fixture(autouse=True)
    def _setup(self, mocker, gmp_app_submitted):
        form_mock = mocker.patch("web.domains.case.export.forms.SubmitGMPForm.is_valid")
        form_mock.return_value = True
        self.app = gmp_app_submitted
        self.form_data = {
            "manufacturer_postcode": "SW1A1AA",  # /PS-IGNORE
            "manufacturer_country": "GB",
            "manufacturer_address_entry_type": "MANUAL",
            "manufacturer_address": "Buckingham Palace, London",
            "responsible_person_postcode": "SW1A1AA",  # /PS-IGNORE
            "responsible_person_address_entry_type": "MANUAL",  # /PS-IGNORE
            "responsible_person_country": "GB",
            "responsible_person_address": "Buckingham Palace, London",
            "is_responsible_person": "yes",
            "gmp_certificate_issued": "BRC_GSOCP",
        }

    def test_gmp_submit_form_clean_ni_postcode_gb_country(self):
        form = SubmitGMPForm(
            instance=self.app,
            data=self.form_data
            | {
                "manufacturer_postcode": "BT43XX",  # /PS-IGNORE
                "responsible_person_postcode": "BT43XX",  # /PS-IGNORE
            },
        )
        form.cleaned_data = form.data
        form.clean()
        assert form.errors["responsible_person_postcode"][0] == "Postcode should not start with BT"
        assert form.errors["manufacturer_postcode"][0] == "Postcode should not start with BT"

    def test_gmp_submit_form_clean_gb_postcode_ni_country(self):
        form = SubmitGMPForm(
            instance=self.app,
            data=self.form_data
            | {
                "manufacturer_country": "NIR",
                "responsible_person_country": "NIR",
            },
        )
        form.cleaned_data = form.data
        form.clean()
        assert form.errors["responsible_person_postcode"][0] == "Postcode must start with BT"
        assert form.errors["manufacturer_postcode"][0] == "Postcode must start with BT"

    def test_gmp_edit_form_clean_manual_address(self):
        data = self.form_data | {
            "manufacturer_address_entry_type": "SEARCH",
            "responsible_person_address_entry_type": "SEARCH",
        }
        form = EditGMPForm(instance=self.app, data=data)
        form.cleaned_data = form.data
        form.clean()
        assert form.cleaned_data["manufacturer_address"] == data["manufacturer_address"]
        assert form.cleaned_data["responsible_person_address"] == data["responsible_person_address"]

    def test_gmp_edit_form_clean_search_address(self):
        data = self.form_data | {
            "manufacturer_address_entry_type": "SEARCH",
            "responsible_person_address_entry_type": "SEARCH",
        }
        form = EditGMPForm(instance=self.app, data=data)
        form.cleaned_data = form.data
        form.clean()
        assert form.cleaned_data["manufacturer_address"] == data["manufacturer_address"]
        assert form.cleaned_data["responsible_person_address"] == data["responsible_person_address"]

    def test_gmp_edit_form_normalize_manual_address(self):
        # Test we can normalise the following unicode character: https://www.codetable.net/decimal/65292
        data = self.form_data | {
            "manufacturer_address": "Buckingham Palace，London，",
            "responsible_person_address": "Buckingham Palace，London，",
        }
        form = EditGMPForm(instance=self.app, data=data)
        form.cleaned_data = form.data
        form.clean()
        assert form.cleaned_data["manufacturer_address"] == "Buckingham Palace, London"
        assert form.cleaned_data["responsible_person_address"] == "Buckingham Palace, London"


def test_edit_gmp_form_readonly_address_input(gmp_app_in_progress):
    gmp_app_in_progress.manufacturer_address_entry_type = AddressEntryType.SEARCH
    gmp_app_in_progress.save()

    form = EditGMPForm(instance=gmp_app_in_progress)
    assert form.fields["manufacturer_address"].widget.attrs["readonly"]

    form = EditGMPForm(
        instance=gmp_app_in_progress,
        data={
            "manufacturer_address_entry_type": AddressEntryType.SEARCH,
            "manufacturer_address": "Test Address",
        },
    )
    assert "readonly" not in form.fields["manufacturer_address"].widget.attrs


@pytest.mark.django_db
def test_edit_cfs_schedule_form_biocidal_claim_helptext(cfs_app_in_progress):
    form = EditCFSScheduleForm(
        instance=cfs_app_in_progress.schedules.first(),
    )
    assert form.fields["biocidal_claim"].help_text == render_to_string(
        "web/domains/case/export/partials/cfs/biocidal_claim_help_text.html"
    )


@pytest.mark.django_db
def test_submit_cfs_schedule_form_biocidal_claim_required(cfs_app_in_progress):
    """Tests that the biocidal_claim field is required when one of the legislations is biocidal."""
    app_schedule = cfs_app_in_progress.schedules.get()
    app_schedule.biocidal_claim = None
    app_schedule.save()

    app_schedule.legislations.add(ProductLegislation.objects.filter(is_biocidal_claim=True)[0])

    form = SubmitCFSScheduleForm(data=model_to_dict(app_schedule), instance=app_schedule)
    assert not form.is_valid()
    assert form.errors["biocidal_claim"][0] == "This field is required."


@pytest.mark.django_db
def test_submit_cfs_form_cptpp_cosmetics(cfs_app_in_progress):
    """Tests that the biocidal_claim field is required when one of the legislations is biocidal."""
    app = cfs_app_in_progress
    country = Country.util.get_cptpp_countries().last()
    app.countries.add(country)

    app_schedule = app.schedules.get()
    app_schedule.legislations.add(
        ProductLegislation.objects.filter(is_eu_cosmetics_regulation=True)[0]
    )

    form = SubmitCFSForm(data={"countries": app.countries.all()}, instance=app)
    assert not form.is_valid()
    assert "This application is not required." in form.errors["countries"][0]


@pytest.mark.django_db
def test_edit_com_form_radio_select_widgets(com_app_in_progress):
    """Tests that the is_pesticide_on_free_sale_uk and is_manufacturer fields are rendered as
    RadioSelectInline widgets and get converted to_python as expected."""
    com_app_in_progress.is_pesticide_on_free_sale_uk = None
    com_app_in_progress.is_manufacturer = None
    com_app_in_progress.save()

    form = EditCOMForm(
        instance=com_app_in_progress,
        data={
            "is_pesticide_on_free_sale_uk": "False",
            "is_manufacturer": "True",
            "product_name": "Test Product",
            "chemical_name": "Test Chemical",
            "manufacturing_process": "Test Process",
        },
    )
    assert isinstance(form.fields["is_pesticide_on_free_sale_uk"].widget, RadioSelectInline)
    assert isinstance(form.fields["is_manufacturer"].widget, RadioSelectInline)

    assert form.is_valid()
    com_app = form.save()

    assert com_app.is_pesticide_on_free_sale_uk is False
    assert com_app.is_manufacturer is True


@pytest.mark.django_db
def test_edit_cfs_schedule_form_goods_export_only_auto_select(cfs_app_in_progress):
    """Tests that the goods_export_only field is automatically selected based on the goods_placed_on_uk_market field."""
    app_schedule = cfs_app_in_progress.schedules.get()

    form = EditCFSScheduleForm(
        instance=app_schedule,
        data={
            "goods_placed_on_uk_market": YesNoChoices.yes,
        },
    )
    assert form.fields["goods_export_only"].disabled
    assert form.is_valid()
    instance = form.save()

    assert instance.goods_export_only == YesNoChoices.no

    form = EditCFSScheduleForm(
        instance=app_schedule,
        data={
            "goods_placed_on_uk_market": YesNoChoices.no,
        },
    )
    assert form.is_valid()
    instance = form.save()

    assert instance.goods_export_only == YesNoChoices.yes


@pytest.mark.parametrize(
    ["cas_numer", "is_valid"],
    [
        # Incorrect basic format
        ("1", False),
        ("1-1", False),
        ("1-1-1", False),
        ("1-12-1", False),
        ("12-1-1", False),
        ("12345678-12-1", False),
        # Real CAS numbers
        ("50-37-3", True),
        ("544-17-2", True),
        ("9048-49-1", True),
        ("19855-56-2", True),
        ("393290-85-2", True),
        ("1234567-89-5", True),
        # Real CAS Numbers (with first digit incremented to fail check digit)
        ("60-37-3", False),
        ("644-17-2", False),
        ("0048-49-1", False),
        ("29855-56-2", False),
        ("493290-85-2", False),
        ("2234567-89-5", False),
    ],
)
def test_cas_number_validation(cas_numer: str, is_valid: bool, cfs_app_in_progress):
    data = {"name": "Test Chemical", "cas_number": cas_numer}

    product = cfs_app_in_progress.schedules.first().products.first()
    form = CFSActiveIngredientForm(data=data, product=product)

    assert form.is_valid() == is_valid


def test_edit_cfs_schedule_manufacturer_form_readonly_address_input(cfs_app_in_progress):
    schedule = cfs_app_in_progress.schedules.first()
    schedule.manufacturer_address_entry_type = AddressEntryType.SEARCH
    schedule.save()

    form = CFSManufacturerDetailsForm(instance=schedule)
    assert form.fields["manufacturer_address"].widget.attrs["readonly"]

    form = CFSManufacturerDetailsForm(
        instance=schedule,
        data={
            "manufacturer_address_entry_type": AddressEntryType.SEARCH,
            "manufacturer_address": "Test Address",
        },
    )
    assert "readonly" not in form.fields["manufacturer_address"].widget.attrs
