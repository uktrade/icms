from web.domains.case._import.fa.forms import (
    ImportContactLegalEntityForm,
    ImportContactPersonForm,
)
from web.models import Country


def test_import_contact_person_form_countries(db):
    form = ImportContactPersonForm()

    # Test all non country values are excluded.
    assert form.fields["country"].queryset.filter(type=Country.SYSTEM).count() == 0


def test_import_contact_legal_entity_form_countries(db):
    form = ImportContactLegalEntityForm()

    # Test all non country values are excluded.
    assert form.fields["country"].queryset.filter(type=Country.SYSTEM).count() == 0
