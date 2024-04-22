import pytest
from django.template.loader import render_to_string

from web.domains.case.export.forms import EditCFScheduleForm, EditCOMForm, SubmitGMPForm
from web.forms.widgets import RadioSelectInline


@pytest.mark.django_db
def test_gmp_form_clean_ni_postcode_gb_country(mocker, gmp_app_submitted):
    form_mock = mocker.patch("web.domains.case.export.forms.SubmitGMPForm.is_valid")
    form_mock.return_value = True
    form = SubmitGMPForm(
        instance=gmp_app_submitted,
        data={
            "manufacturer_postcode": "BT43XX",  # /PS-IGNORE
            "manufacturer_country": "GB",
            "responsible_person_postcode": "BT43XX",  # /PS-IGNORE
            "responsible_person_country": "GB",
            "is_responsible_person": "yes",
            "gmp_certificate_issued": "BRC_GSOCP",
        },
    )
    form.cleaned_data = form.data
    form.clean()
    assert form.errors["responsible_person_postcode"][0] == "Postcode should not start with BT"
    assert form.errors["manufacturer_postcode"][0] == "Postcode should not start with BT"


@pytest.mark.django_db
def test_gmp_form_clean_gb_postcode_ni_country(mocker, gmp_app_submitted):
    form_mock = mocker.patch("web.domains.case.export.forms.SubmitGMPForm.is_valid")
    form_mock.return_value = True

    form = SubmitGMPForm(
        instance=gmp_app_submitted,
        data={
            "manufacturer_postcode": "SW1A1AA",  # /PS-IGNORE
            "manufacturer_country": "NIR",
            "responsible_person_postcode": "SW1A1AA",  # /PS-IGNORE
            "responsible_person_country": "NIR",
            "is_responsible_person": "yes",
            "gmp_certificate_issued": "BRC_GSOCP",
        },
    )
    form.cleaned_data = form.data
    form.clean()
    assert form.errors["responsible_person_postcode"][0] == "Postcode must start with BT"
    assert form.errors["manufacturer_postcode"][0] == "Postcode must start with BT"


@pytest.mark.django_db
def test_edit_cfs_schedule_form_biocidal_claim_helptext(cfs_app_in_progress):
    form = EditCFScheduleForm(
        instance=cfs_app_in_progress.schedules.first(),
    )
    assert form.fields["biocidal_claim"].help_text == render_to_string(
        "web/domains/case/export/partials/cfs/biocidal_claim_help_text.html"
    )


@pytest.mark.django_db
def test_edit_cfs_schedule_form_biocidal_claim_required(cfs_app_in_progress):
    """Tests that the biocidal_claim field is required when one of the legislations is biocidal."""
    app_schedule = cfs_app_in_progress.schedules.get()
    chosen_legislation = app_schedule.legislations.get()
    chosen_legislation.is_biocidal_claim = True
    chosen_legislation.save()

    app_schedule.refresh_from_db()

    form = EditCFScheduleForm(
        instance=app_schedule,
        data={
            "biocidal_claim": "",
            "legislations": [chosen_legislation.pk],
        },
    )
    assert not form.is_valid()
    assert form.errors["biocidal_claim"][0] == "This field is required."


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
