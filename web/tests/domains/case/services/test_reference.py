import datetime as dt
import re

import pytest
from django.utils import timezone

from web.domains.case.services import document_pack, reference
from web.flow.models import ProcessTypes
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    Country,
    DFLApplication,
    ExportApplicationType,
    ImportApplicationType,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    PriorSurveillanceApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    TextilesApplication,
    UniqueReference,
    VariationRequest,
    WoodQuotaApplication,
)
from web.tests.helpers import add_variation_request_to_app

CASE_REF_PATTERN = re.compile(
    r"""
        [a-z]+  # Prefix
        /       # Separator
        \d+     # Year
        /       # Separator
        \d+     # reference
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)


@pytest.mark.django_db
def test_digits(lock_manager):
    # put in two rows, neither of which should match the later calls
    year = timezone.now().year
    UniqueReference.objects.create(prefix="bluu", year=None, reference=500)
    UniqueReference.objects.create(prefix="blaa", year=year, reference=500)

    ref1 = reference._get_next_reference(lock_manager, prefix="blaa", use_year=False)
    assert reference._get_reference_string(ref1, False, min_digits=0) == "blaa/1"

    ref2 = reference._get_next_reference(lock_manager, prefix="blaa", use_year=False)
    assert reference._get_reference_string(ref2, False, min_digits=5) == "blaa/00002"


@pytest.mark.django_db
def test_digits_overflow(lock_manager):
    UniqueReference.objects.create(prefix="bluu", year=None, reference=500)

    ref = reference._get_next_reference(lock_manager, prefix="bluu", use_year=False)
    assert reference._get_reference_string(ref, False, min_digits=2) == "bluu/501"


@pytest.mark.django_db
def test_year(lock_manager):
    year = timezone.now().year

    ref1 = reference._get_next_reference(lock_manager, prefix="blii", use_year=True)
    assert reference._get_reference_string(ref1, True, min_digits=3) == f"blii/{year}/001"

    ref2 = reference._get_next_reference(lock_manager, prefix="blii", use_year=True)
    assert reference._get_reference_string(ref2, True, min_digits=4) == f"blii/{year}/0002"


def test_get_application_case_and_licence_references(
    db, importer_one_contact, importer, office, exporter, exporter_office, lock_manager
):
    iat = ImportApplicationType.Types
    iast = ImportApplicationType.SubTypes
    eat = ExportApplicationType.Types

    shared = {"created_by": importer_one_contact, "last_updated_by": importer_one_contact}
    import_common = shared | {"importer": importer, "importer_office": office}
    export_common = shared | {"exporter": exporter, "exporter_office": exporter_office}

    dfl_app = DFLApplication.objects.create(
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.FIREARMS, sub_type=iast.DFL),
        **import_common,
    )
    dfl_app.licences.create(issue_paper_licence_only=False)

    oil_app = OpenIndividualLicenceApplication.objects.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.FIREARMS, sub_type=iast.OIL),
        **import_common,
    )
    oil_app.licences.create(issue_paper_licence_only=False)

    sil_app = SILApplication.objects.create(
        process_type=SILApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.FIREARMS, sub_type=iast.SIL),
        **import_common,
    )
    sil_app.licences.create(issue_paper_licence_only=False)

    opt_app = OutwardProcessingTradeApplication.objects.create(
        process_type=OutwardProcessingTradeApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.OPT),
        **import_common,
    )
    opt_app.licences.create(issue_paper_licence_only=True)

    sanction_app = SanctionsAndAdhocApplication.objects.create(
        process_type=SanctionsAndAdhocApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.SANCTION_ADHOC),
        **import_common,
    )
    sanction_app.licences.create(issue_paper_licence_only=False)

    sps_app = PriorSurveillanceApplication.objects.create(
        process_type=PriorSurveillanceApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.SPS),
        **import_common,
    )
    sps_app.licences.create(issue_paper_licence_only=False)

    textile_app = TextilesApplication.objects.create(
        process_type=TextilesApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.TEXTILES),
        **import_common,
    )
    textile_app.licences.create(issue_paper_licence_only=False)

    wood_app = WoodQuotaApplication.objects.create(
        process_type=WoodQuotaApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.WOOD_QUOTA),
        **import_common,
    )
    wood_app.licences.create(issue_paper_licence_only=True)

    com_app = CertificateOfManufactureApplication.objects.create(
        process_type=CertificateOfManufactureApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(type_code=eat.MANUFACTURE),
        **export_common,
    )
    com_app.certificates.create()

    cfs_app = CertificateOfFreeSaleApplication.objects.create(
        process_type=CertificateOfFreeSaleApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(type_code=eat.FREE_SALE),
        **export_common,
    )
    cfs_app.certificates.create()

    gmp_app = CertificateOfGoodManufacturingPracticeApplication.objects.create(
        process_type=CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(type_code=eat.GMP),
        **export_common,
    )
    gmp_app.certificates.create()

    year = dt.date.today().year

    dfl_app.reference = reference.get_application_case_reference(lock_manager, dfl_app)
    dfl_app.save()
    assert dfl_app.reference == f"IMA/{year}/00001"

    oil_app.reference = reference.get_application_case_reference(lock_manager, oil_app)
    oil_app.save()
    assert oil_app.reference == f"IMA/{year}/00002"

    sil_app.reference = reference.get_application_case_reference(lock_manager, sil_app)
    sil_app.save()
    assert sil_app.reference == f"IMA/{year}/00003"

    opt_app.reference = reference.get_application_case_reference(lock_manager, opt_app)
    opt_app.save()
    assert opt_app.reference == f"IMA/{year}/00004"

    sanction_app.reference = reference.get_application_case_reference(lock_manager, sanction_app)
    sanction_app.save()
    assert sanction_app.reference == f"IMA/{year}/00005"

    sps_app.reference = reference.get_application_case_reference(lock_manager, sps_app)
    sps_app.save()
    assert sps_app.reference == f"IMA/{year}/00006"

    textile_app.reference = reference.get_application_case_reference(lock_manager, textile_app)
    textile_app.save()
    assert textile_app.reference == f"IMA/{year}/00007"

    wood_app.reference = reference.get_application_case_reference(lock_manager, wood_app)
    wood_app.save()
    assert wood_app.reference == f"IMA/{year}/00008"

    com_app.reference = reference.get_application_case_reference(lock_manager, com_app)
    com_app.save()
    assert com_app.reference == f"CA/{year}/00001"

    cfs_app.reference = reference.get_application_case_reference(lock_manager, cfs_app)
    cfs_app.save()
    assert cfs_app.reference == f"CA/{year}/00002"

    gmp_app.reference = reference.get_application_case_reference(lock_manager, gmp_app)
    gmp_app.save()
    assert gmp_app.reference == f"GA/{year}/00001"

    import_apps = [
        dfl_app,
        oil_app,
        sil_app,
        opt_app,
        sanction_app,
        sps_app,
        textile_app,
        wood_app,
    ]

    for app in import_apps:
        licence = document_pack.pack_draft_get(app)
        ref = reference.get_import_licence_reference(lock_manager, app, licence)
        document_pack.doc_ref_licence_create(licence, ref)

    doc = _get_licence_document(dfl_app)
    assert doc.reference == "GBSIL0000001B"

    doc = _get_licence_document(oil_app)
    assert doc.reference == "GBOIL0000002C"

    doc = _get_licence_document(sil_app)
    assert doc.reference == "GBSIL0000003D"

    doc = _get_licence_document(opt_app)
    assert doc.reference == "0000004E"

    doc = _get_licence_document(sanction_app)
    assert doc.reference == "GBSAN0000005F"

    doc = _get_licence_document(sps_app)
    assert doc.reference == "GBAOG0000006G"

    doc = _get_licence_document(textile_app)
    assert doc.reference == "GBTEX0000007H"

    doc = _get_licence_document(wood_app)
    assert doc.reference == "0000008X"

    cert_country_1 = Country.objects.first()
    cert_country_2 = Country.objects.last()
    assert cert_country_1 != cert_country_2

    for cert_country in [cert_country_1, cert_country_2]:
        for app in [com_app, cfs_app, gmp_app]:
            certificate = document_pack.pack_draft_get(app)
            ref = reference.get_export_certificate_reference(lock_manager, app)
            document_pack.doc_ref_certificate_create(certificate, ref, country=cert_country)

    today = dt.date.today()

    doc = _get_certificate_document(com_app, cert_country_1)
    doc.reference = f"COM/{today.year}/00001"

    doc = _get_certificate_document(com_app, cert_country_2)
    doc.reference = f"COM/{today.year}/00002"

    doc = _get_certificate_document(cfs_app, cert_country_1)
    doc.reference = f"CFS/{today.year}/00001"

    doc = _get_certificate_document(cfs_app, cert_country_2)
    doc.reference = f"CFS/{today.year}/00002"

    doc = _get_certificate_document(gmp_app, cert_country_1)
    doc.reference = f"GMP/{today.year}/00001"

    doc = _get_certificate_document(gmp_app, cert_country_2)
    doc.reference = f"GMP/{today.year}/00002"


def test_import_application_licence_reference_is_reused(
    db, importer, office, importer_one_contact, lock_manager
):
    app = DFLApplication.objects.create(
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
        ),
    )
    app.licences.create()
    assert app.licence_reference is None

    # This should set the reference
    licence = document_pack.pack_draft_get(app)
    ref = reference.get_import_licence_reference(lock_manager, app, licence)

    assert ref == "GBSIL0000001B"
    assert app.licence_reference.prefix == UniqueReference.Prefix.IMPORT_LICENCE_DOCUMENT
    assert app.licence_reference.reference == 1

    # This should now reuse the same reference
    licence = document_pack.pack_draft_get(app)
    ref = reference.get_import_licence_reference(lock_manager, app, licence)
    assert ref == "GBSIL0000001B"
    assert app.licence_reference.prefix == UniqueReference.Prefix.IMPORT_LICENCE_DOCUMENT
    assert app.licence_reference.reference == 1


def test_get_export_certificate_reference_invalid_process_type(
    db, importer, office, importer_one_contact, lock_manager
):
    app = DFLApplication.objects.create(
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
        ),
    )
    with pytest.raises(
        ValueError,
        match=f"Invalid process_type {app.process_type}: ExportApplication process_type is required.",
    ):
        reference.get_export_certificate_reference(lock_manager, app)


def _get_licence_document(app):
    pack = document_pack.pack_draft_get(app)

    return document_pack.doc_ref_licence_get(pack)


def _get_certificate_document(app, country):
    pack = document_pack.pack_draft_get(app)

    return document_pack.doc_ref_certificate_get(pack, country)


def test_unallocated_application_raises_error(wood_app_in_progress):
    with pytest.raises(ValueError, match="Application has not been assigned yet."):
        reference.get_variation_request_case_reference(wood_app_in_progress)


def test_get_wood_app_variation_request_case_reference(wood_app_submitted, ilb_admin_user):
    initial_reference = wood_app_submitted.get_reference()
    assert re.match(CASE_REF_PATTERN, initial_reference)

    # Add a variation request
    add_variation_request_to_app(wood_app_submitted, ilb_admin_user)

    expected_reference = f"{initial_reference}/1"
    actual_reference = reference.get_variation_request_case_reference(wood_app_submitted)

    assert expected_reference == actual_reference


def test_get_variation_request_case_reference_with_existing_variations(
    wood_app_submitted, ilb_admin_user
):
    initial_reference = wood_app_submitted.get_reference()

    # Update an existing app reference (and set some dummy variation requests)
    for i in range(5):
        add_variation_request_to_app(
            wood_app_submitted,
            ilb_admin_user,
            f"What varied {i + 1}",
            VariationRequest.Statuses.CANCELLED,
        )
    wood_app_submitted.reference = f"{initial_reference}/5"
    wood_app_submitted.save()

    # Add a new vr so that the suffix will change
    add_variation_request_to_app(wood_app_submitted, ilb_admin_user)

    expected_reference = f"{initial_reference}/6"
    actual_reference = reference.get_variation_request_case_reference(wood_app_submitted)

    assert expected_reference == actual_reference


def test_get_com_app_variation_request_case_reference(com_app_submitted, ilb_admin_user):
    initial_reference = com_app_submitted.get_reference()
    assert re.match(CASE_REF_PATTERN, initial_reference)

    # Add a variation request
    add_variation_request_to_app(com_app_submitted, ilb_admin_user)

    expected_reference = f"{initial_reference}/1"
    actual_reference = reference.get_variation_request_case_reference(com_app_submitted)

    assert expected_reference == actual_reference


def test_get_com_app_variation_request_case_reference_with_existing_variations(
    com_app_submitted, ilb_admin_user
):
    initial_reference = com_app_submitted.get_reference()

    # Update an existing app reference (and set some dummy variation requests)
    for i in range(5):
        add_variation_request_to_app(
            com_app_submitted,
            ilb_admin_user,
            what_varied=f"What varied {i + 1}",
            status=VariationRequest.Statuses.CLOSED,
        )
    com_app_submitted.reference = f"{initial_reference}/5"
    com_app_submitted.save()

    # Add a new vr so that the suffix will change
    open_vr = add_variation_request_to_app(com_app_submitted, ilb_admin_user)

    expected_reference = f"{initial_reference}/6"
    actual_reference = reference.get_variation_request_case_reference(com_app_submitted)

    assert expected_reference == actual_reference

    # Update the OPEN variation request to CANCELLED.
    open_vr.status = VariationRequest.Statuses.CANCELLED
    open_vr.save()

    expected_reference = f"{initial_reference}/5"
    actual_reference = reference.get_variation_request_case_reference(com_app_submitted)

    assert expected_reference == actual_reference


def test_get_com_app_variation_request_count_is_zero(com_app_submitted, ilb_admin_user):
    initial_reference = com_app_submitted.get_reference()
    add_variation_request_to_app(
        com_app_submitted,
        ilb_admin_user,
        "A variation request that was opened and cancelled",
        VariationRequest.Statuses.CANCELLED,
    )

    expected_reference = initial_reference
    actual_reference = reference.get_variation_request_case_reference(com_app_submitted)

    assert expected_reference == actual_reference


def test_case_reference_correct_with_no_valid_variation_requests(com_app_submitted, ilb_admin_user):
    add_variation_request_to_app(
        com_app_submitted, ilb_admin_user, status=VariationRequest.Statuses.CANCELLED
    )
    add_variation_request_to_app(
        com_app_submitted, ilb_admin_user, status=VariationRequest.Statuses.CANCELLED
    )
    add_variation_request_to_app(
        com_app_submitted, ilb_admin_user, status=VariationRequest.Statuses.CANCELLED
    )

    # This tests there is no variation part in the case reference
    assert re.match(CASE_REF_PATTERN, com_app_submitted.get_reference())


def test_get_mailshot_reference(db, lock_manager):
    expected = "MAIL/1"
    actual = reference.get_mailshot_reference(lock_manager)

    assert expected == actual


def test_get_importer_access_request_reference(db, lock_manager):
    expected = "IAR/1"
    actual = reference.get_importer_access_request_reference(lock_manager)

    assert expected == actual


def test_get_exporter_access_request_reference(db, lock_manager):
    expected = "EAR/1"
    actual = reference.get_exporter_access_request_reference(lock_manager)

    assert expected == actual


@pytest.mark.parametrize(
    "licence_type, process_type, next_sequence_value, expected_reference",
    [
        ("electronic", ProcessTypes.FA_DFL, 1, "GBSIL0000001B"),
        ("electronic", ProcessTypes.FA_OIL, 2, "GBOIL0000002C"),
        ("electronic", ProcessTypes.FA_SIL, 3, "GBSIL0000003D"),
        ("electronic", ProcessTypes.SPS, 4, "GBAOG0000004E"),
        ("electronic", ProcessTypes.SANCTIONS, 5, "GBSAN0000005F"),
        ("electronic", ProcessTypes.TEXTILES, 6, "GBTEX0000006G"),
        ("paper", ProcessTypes.FA_DFL, 7, "0000007H"),
        ("paper", ProcessTypes.FA_OIL, 8, "0000008X"),
        ("paper", ProcessTypes.FA_SIL, 9, "0000009J"),
        ("paper", ProcessTypes.SPS, 10, "0000010K"),
        ("paper", ProcessTypes.SANCTIONS, 11, "0000011L"),
        ("paper", ProcessTypes.TEXTILES, 12, "0000012M"),
        ("electronic", ProcessTypes.NUCLEAR, 13, "GBSIL0000013A"),
    ],
)
def test_get_import_application_licence_reference(
    licence_type, process_type, next_sequence_value, expected_reference
):
    actual_reference = reference._get_licence_reference(
        licence_type, process_type, next_sequence_value
    )
    assert expected_reference == actual_reference, f"Expected failed {expected_reference}"
