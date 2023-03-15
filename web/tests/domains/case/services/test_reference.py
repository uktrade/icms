import datetime
import re

import pytest
from django.utils import timezone

from web.domains.case.services import document_pack, reference
from web.flow.models import ProcessTypes
from web.models import (
    CaseReference,
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    Country,
    DerogationsApplication,
    DFLApplication,
    ExportApplicationType,
    ImportApplicationType,
    IronSteelApplication,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    PriorSurveillanceApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    TextilesApplication,
    VariationRequest,
    WoodQuotaApplication,
)

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
    CaseReference.objects.create(prefix="bluu", year=None, reference=500)
    CaseReference.objects.create(prefix="blaa", year=year, reference=500)

    ref1 = reference._get_next_reference(lock_manager, prefix="blaa", use_year=False)
    assert reference._get_reference_string(ref1, False, min_digits=0) == "blaa/1"

    ref2 = reference._get_next_reference(lock_manager, prefix="blaa", use_year=False)
    assert reference._get_reference_string(ref2, False, min_digits=5) == "blaa/00002"


@pytest.mark.django_db
def test_digits_overflow(lock_manager):
    CaseReference.objects.create(prefix="bluu", year=None, reference=500)

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
    db, test_import_user, importer, office, exporter, exporter_office, lock_manager
):
    iat = ImportApplicationType.Types
    iast = ImportApplicationType.SubTypes
    eat = ExportApplicationType.Types

    shared = {"created_by": test_import_user, "last_updated_by": test_import_user}
    import_common = shared | {"importer": importer, "importer_office": office}
    export_common = shared | {"exporter": exporter, "exporter_office": exporter_office}

    derogation_app = DerogationsApplication.objects.create(
        process_type=DerogationsApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.DEROGATION),
        **import_common,
    )
    derogation_app.licences.create(issue_paper_licence_only=False)

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

    iron_app = IronSteelApplication.objects.create(
        process_type=IronSteelApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.IRON_STEEL),
        **import_common,
    )
    iron_app.licences.create(issue_paper_licence_only=False)

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

    year = datetime.date.today().year

    derogation_app.reference = reference.get_application_case_reference(
        lock_manager, derogation_app
    )
    derogation_app.save()
    assert derogation_app.reference == f"IMA/{year}/00001"

    dfl_app.reference = reference.get_application_case_reference(lock_manager, dfl_app)
    dfl_app.save()
    assert dfl_app.reference == f"IMA/{year}/00002"

    oil_app.reference = reference.get_application_case_reference(lock_manager, oil_app)
    oil_app.save()
    assert oil_app.reference == f"IMA/{year}/00003"

    sil_app.reference = reference.get_application_case_reference(lock_manager, sil_app)
    sil_app.save()
    assert sil_app.reference == f"IMA/{year}/00004"

    iron_app.reference = reference.get_application_case_reference(lock_manager, iron_app)
    iron_app.save()
    assert iron_app.reference == f"IMA/{year}/00005"

    opt_app.reference = reference.get_application_case_reference(lock_manager, opt_app)
    opt_app.save()
    assert opt_app.reference == f"IMA/{year}/00006"

    sanction_app.reference = reference.get_application_case_reference(lock_manager, sanction_app)
    sanction_app.save()
    assert sanction_app.reference == f"IMA/{year}/00007"

    sps_app.reference = reference.get_application_case_reference(lock_manager, sps_app)
    sps_app.save()
    assert sps_app.reference == f"IMA/{year}/00008"

    textile_app.reference = reference.get_application_case_reference(lock_manager, textile_app)
    textile_app.save()
    assert textile_app.reference == f"IMA/{year}/00009"

    wood_app.reference = reference.get_application_case_reference(lock_manager, wood_app)
    wood_app.save()
    assert wood_app.reference == f"IMA/{year}/00010"

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
        derogation_app,
        dfl_app,
        oil_app,
        sil_app,
        iron_app,
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

    doc = _get_licence_document(derogation_app)
    assert doc.reference == "GBSAN0000001B"

    doc = _get_licence_document(dfl_app)
    assert doc.reference == "GBSIL0000002C"

    doc = _get_licence_document(oil_app)
    assert doc.reference == "GBOIL0000003D"

    doc = _get_licence_document(sil_app)
    assert doc.reference == "GBSIL0000004E"

    doc = _get_licence_document(iron_app)
    assert doc.reference == "GBAOG0000005F"

    doc = _get_licence_document(opt_app)
    assert doc.reference == "0000006G"

    doc = _get_licence_document(sanction_app)
    assert doc.reference == "GBSAN0000007H"

    doc = _get_licence_document(sps_app)
    assert doc.reference == "GBAOG0000008X"

    doc = _get_licence_document(textile_app)
    assert doc.reference == "GBTEX0000009J"

    doc = _get_licence_document(wood_app)
    assert doc.reference == "0000010K"

    cert_country = Country.objects.first()
    for app in [com_app, cfs_app, gmp_app]:
        certificate = document_pack.pack_draft_get(app)
        ref = reference.get_export_certificate_reference(lock_manager, app)
        document_pack.doc_ref_certificate_create(certificate, ref, country=cert_country)

    today = datetime.date.today()

    doc = _get_certificate_document(com_app, cert_country)
    doc.reference = f"COM/{today.year}/00001"

    doc = _get_certificate_document(cfs_app, cert_country)
    doc.reference = f"CFS/{today.year}/00002"

    doc = _get_certificate_document(gmp_app, cert_country)
    doc.reference = f"GMP/{today.year}/00003"


def test_import_application_licence_reference_is_reused(
    db, importer, office, test_import_user, lock_manager
):
    app = DFLApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
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
    assert app.licence_reference.prefix == CaseReference.Prefix.IMPORT_LICENCE_DOCUMENT
    assert app.licence_reference.reference == 1

    # This should now reuse the same reference
    licence = document_pack.pack_draft_get(app)
    ref = reference.get_import_licence_reference(lock_manager, app, licence)
    assert ref == "GBSIL0000001B"
    assert app.licence_reference.prefix == CaseReference.Prefix.IMPORT_LICENCE_DOCUMENT
    assert app.licence_reference.reference == 1


def _get_licence_document(app):
    pack = document_pack.pack_draft_get(app)

    return document_pack.doc_ref_licence_get(pack)


def _get_certificate_document(app, country):
    pack = document_pack.pack_draft_get(app)

    return document_pack.doc_ref_certificate_get(pack, country)


def test_unallocated_application_raises_error(wood_app_in_progress):
    with pytest.raises(ValueError, match="Application has not been assigned yet."):
        reference.get_variation_request_case_reference(wood_app_in_progress)


def test_get_wood_app_variation_request_case_reference(wood_app_submitted, test_icms_admin_user):
    initial_reference = wood_app_submitted.get_reference()
    assert re.match(CASE_REF_PATTERN, initial_reference)

    # Add a variation request
    _add_variation_request(wood_app_submitted, test_icms_admin_user)

    expected_reference = f"{initial_reference}/1"
    actual_reference = reference.get_variation_request_case_reference(wood_app_submitted)

    assert expected_reference == actual_reference


def test_get_variation_request_case_reference_with_existing_variations(
    wood_app_submitted, test_icms_admin_user
):
    initial_reference = wood_app_submitted.get_reference()

    # Update an existing app reference (and set some dummy variation requests)
    for i in range(5):
        _add_variation_request(
            wood_app_submitted,
            test_icms_admin_user,
            f"What varied {i + 1}",
            VariationRequest.CANCELLED,
        )
    wood_app_submitted.reference = f"{initial_reference}/5"
    wood_app_submitted.save()

    # Add a new vr so that the suffix will change
    _add_variation_request(wood_app_submitted, test_icms_admin_user)

    expected_reference = f"{initial_reference}/6"
    actual_reference = reference.get_variation_request_case_reference(wood_app_submitted)

    assert expected_reference == actual_reference


def test_get_com_app_variation_request_case_reference(com_app_submitted, test_icms_admin_user):
    initial_reference = com_app_submitted.get_reference()
    assert re.match(CASE_REF_PATTERN, initial_reference)

    # Add a variation request
    _add_variation_request(com_app_submitted, test_icms_admin_user)

    expected_reference = f"{initial_reference}/1"
    actual_reference = reference.get_variation_request_case_reference(com_app_submitted)

    assert expected_reference == actual_reference


def test_get_com_app_variation_request_case_reference_with_existing_variations(
    com_app_submitted, test_icms_admin_user
):
    initial_reference = com_app_submitted.get_reference()

    # Update an existing app reference (and set some dummy variation requests)
    for i in range(5):
        _add_variation_request(
            com_app_submitted,
            test_icms_admin_user,
            f"What varied {i + 1}",
            VariationRequest.CLOSED,
        )
    com_app_submitted.reference = f"{initial_reference}/5"
    com_app_submitted.save()

    # Add a new vr so that the suffix will change
    open_vr = _add_variation_request(com_app_submitted, test_icms_admin_user)

    expected_reference = f"{initial_reference}/6"
    actual_reference = reference.get_variation_request_case_reference(com_app_submitted)

    assert expected_reference == actual_reference

    # Update the OPEN variation request to CANCELLED.
    open_vr.status = VariationRequest.CANCELLED
    open_vr.save()

    expected_reference = f"{initial_reference}/5"
    actual_reference = reference.get_variation_request_case_reference(com_app_submitted)

    assert expected_reference == actual_reference


def test_get_com_app_variation_request_count_is_zero(com_app_submitted, test_icms_admin_user):
    initial_reference = com_app_submitted.get_reference()
    _add_variation_request(
        com_app_submitted,
        test_icms_admin_user,
        "A variation request that was opened and cancelled",
        VariationRequest.CANCELLED,
    )

    expected_reference = initial_reference
    actual_reference = reference.get_variation_request_case_reference(com_app_submitted)

    assert expected_reference == actual_reference


def test_case_reference_correct_with_no_valid_variation_requests(
    com_app_submitted, test_icms_admin_user
):
    _add_variation_request(
        com_app_submitted, test_icms_admin_user, status=VariationRequest.CANCELLED
    )
    _add_variation_request(
        com_app_submitted, test_icms_admin_user, status=VariationRequest.CANCELLED
    )
    _add_variation_request(
        com_app_submitted, test_icms_admin_user, status=VariationRequest.CANCELLED
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


def _add_variation_request(
    app, user, what_varied="Dummy what_varied", status=VariationRequest.OPEN
):
    return app.variation_requests.create(
        status=status,
        what_varied=what_varied,
        why_varied="Dummy why_varied",
        when_varied=datetime.date.today(),
        requested_by=user,
    )


@pytest.mark.parametrize(
    "licence_type, process_type, next_sequence_value, expected_reference",
    [
        ("electronic", ProcessTypes.DEROGATIONS, 1, "GBSAN0000001B"),
        ("electronic", ProcessTypes.FA_DFL, 2, "GBSIL0000002C"),
        ("electronic", ProcessTypes.FA_OIL, 3, "GBOIL0000003D"),
        ("electronic", ProcessTypes.FA_SIL, 4, "GBSIL0000004E"),
        ("electronic", ProcessTypes.IRON_STEEL, 5, "GBAOG0000005F"),
        ("electronic", ProcessTypes.SPS, 6, "GBAOG0000006G"),
        ("electronic", ProcessTypes.SANCTIONS, 7, "GBSAN0000007H"),
        ("electronic", ProcessTypes.TEXTILES, 8, "GBTEX0000008X"),
        ("paper", ProcessTypes.DEROGATIONS, 9, "0000009J"),
        ("paper", ProcessTypes.FA_DFL, 10, "0000010K"),
        ("paper", ProcessTypes.FA_OIL, 11, "0000011L"),
        ("paper", ProcessTypes.FA_SIL, 12, "0000012M"),
        ("paper", ProcessTypes.IRON_STEEL, 13, "0000013A"),
        ("paper", ProcessTypes.SPS, 14, "0000014B"),
        ("paper", ProcessTypes.SANCTIONS, 15, "0000015C"),
        ("paper", ProcessTypes.TEXTILES, 16, "0000016D"),
    ],
)
def test_get_import_application_licence_reference(
    licence_type, process_type, next_sequence_value, expected_reference
):
    actual_reference = reference._get_licence_reference(
        licence_type, process_type, next_sequence_value
    )
    assert expected_reference == actual_reference, f"Expected failed {expected_reference}"


@pytest.mark.parametrize(
    "process_type, next_sequence_value, expected_reference",
    [
        (ProcessTypes.COM, 1, f"COM/{datetime.date.today().year}/00001"),
        (ProcessTypes.CFS, 2, f"CFS/{datetime.date.today().year}/00002"),
        (ProcessTypes.GMP, 3, f"GMP/{datetime.date.today().year}/00003"),
    ],
)
def test_get_export_application_licence_reference(
    process_type, next_sequence_value, expected_reference
):
    actual_reference = reference._get_certificate_reference(process_type, next_sequence_value)

    assert expected_reference == actual_reference, f"Expected failed {expected_reference}"
