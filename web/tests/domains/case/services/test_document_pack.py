from web.domains.case._import.models import DocumentPackBase
from web.domains.case.services import document_pack


def test_set_application_licence_or_certificate_active(wood_app_submitted):
    assert wood_app_submitted.licences.count() == 1

    licence_1 = document_pack.pack_draft_get(wood_app_submitted)
    assert licence_1.status == DocumentPackBase.Status.DRAFT

    # Set this licence as active so we can test making the second licence active
    document_pack.pack_draft_set_active(wood_app_submitted)
    licence_1.refresh_from_db()
    assert licence_1.status == DocumentPackBase.Status.ACTIVE
    assert licence_1.case_reference == wood_app_submitted.reference

    # Create a new draft licence
    licence_2 = wood_app_submitted.licences.create()
    assert licence_2.status == DocumentPackBase.Status.DRAFT

    # Fake a variation request for the case
    wood_app_submitted.reference = f"{wood_app_submitted.reference}/1"
    wood_app_submitted.save()

    # Test licence 2 is now active and licence 1 is archived.
    document_pack.pack_draft_set_active(wood_app_submitted)
    licence_1.refresh_from_db()
    licence_2.refresh_from_db()

    assert licence_1.status == DocumentPackBase.Status.ARCHIVED
    assert licence_2.status == DocumentPackBase.Status.ACTIVE

    # Test the second licence has the updated case reference
    assert licence_2.case_reference == wood_app_submitted.reference