import logging

from web.domains.case._import.forms import (
    CoverLetterForm,
    CreateImportApplicationForm,
    CreateWoodQuotaApplicationForm,
)

logger = logging.getLogger(__name__)


class TestCreateOpenIndividualImportLicenceForm:
    def test_form_valid(self, db, importer, office, importer_one_contact):
        form = CreateImportApplicationForm(
            data={
                "importer": importer.pk,
                "importer_office": office.pk,
            },
            user=importer_one_contact,
        )

        assert form.is_valid() is True

    def test_agent_form_valid(
        self,
        db,
        importer,
        office,
        agent_importer,
        importer_one_agent_office,
        importer_one_agent_one_contact,
    ):
        form = CreateImportApplicationForm(
            data={
                "importer": importer.pk,
                "importer_office": office.pk,
                "agent": agent_importer.pk,
                "agent_office": importer_one_agent_office.pk,
            },
            user=importer_one_agent_one_contact,
        )
        assert form.is_valid(), form.errors

    def test_invalid_form_message(self, importer_one_contact):
        form = CreateImportApplicationForm(data={}, user=importer_one_contact)

        assert len(form.errors) == 2
        assert form.errors["importer"][0] == "You must enter this item"

    def test_wood_application_valid_for_ni_importer(
        self, db, importer, office, importer_one_contact
    ):
        form = CreateWoodQuotaApplicationForm(
            data={
                "importer": importer.pk,
                "importer_office": office.pk,
            },
            user=importer_one_contact,
        )

        assert form.is_valid(), "Form has errors"

    def test_wood_application_invalid_for_english_importer(
        self, db, importer, office, importer_one_contact
    ):
        office.postcode = "S410SG"  # /PS-IGNORE
        office.save()

        form = CreateWoodQuotaApplicationForm(
            data={
                "importer": importer.pk,
                "importer_office": office.pk,
            },
            user=importer_one_contact,
        )

        assert form.has_error("importer_office") is True
        assert len(form.errors) == 1

        error_message = form.errors["importer_office"][0]
        assert error_message == "Wood applications can only be made for Northern Ireland traders."


def test_cover_letter_form_valid(fa_dfl_app_submitted):
    post_data = {"cover_letter_text": "Test cover letter [[LICENCE_NUMBER]]"}
    form = CoverLetterForm(post_data, instance=fa_dfl_app_submitted)
    assert form.is_valid() is True


def test_cover_letter_form_invalid(fa_dfl_app_submitted):
    post_data = {"cover_letter_text": "Test cover letter [[INVALID]]"}
    form = CoverLetterForm(post_data, instance=fa_dfl_app_submitted)
    assert form.is_valid() is False

    error_message = form.errors["cover_letter_text"][0]
    assert error_message == "The following placeholders are invalid: [[INVALID]]"
