from web.domains.case._import.models import CaseLicenceCertificateBase
from web.domains.case.utils import set_application_licence_or_certificate_active


def test_set_application_licence_or_certificate_active(wood_app_submitted):
    assert wood_app_submitted.licences.count() == 1

    licence_1 = wood_app_submitted.get_most_recent_licence()
    assert licence_1.status == CaseLicenceCertificateBase.Status.DRAFT

    # Set this licence as active so we can test making the second licence active
    set_application_licence_or_certificate_active(wood_app_submitted)
    licence_1.refresh_from_db()
    assert licence_1.status == CaseLicenceCertificateBase.Status.ACTIVE

    # Create a new draft licence
    licence_2 = wood_app_submitted.licences.create()
    assert licence_2.status == CaseLicenceCertificateBase.Status.DRAFT

    # Test licence 2 is now active and licence 1 is archived.
    set_application_licence_or_certificate_active(wood_app_submitted)
    licence_1.refresh_from_db()
    licence_2.refresh_from_db()

    assert licence_1.status == CaseLicenceCertificateBase.Status.ARCHIVED
    assert licence_2.status == CaseLicenceCertificateBase.Status.ACTIVE
