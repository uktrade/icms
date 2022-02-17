import datetime
import re
from unittest.mock import Mock

import pytest
from django.utils import timezone

from web.domains.case.models import VariationRequest
from web.domains.case.utils import (
    allocate_case_reference,
    get_import_application_licence_reference,
    get_variation_request_case_reference,
)
from web.flow.models import ProcessTypes
from web.models.models import CaseReference


@pytest.fixture
def lock_manager():
    return Mock()


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

    ref1 = allocate_case_reference(
        lock_manager=lock_manager, prefix="blaa", use_year=False, min_digits=0
    )
    assert ref1 == "blaa/1"

    ref2 = allocate_case_reference(
        lock_manager=lock_manager, prefix="blaa", use_year=False, min_digits=5
    )
    assert ref2 == "blaa/00002"


@pytest.mark.django_db
def test_digits_overflow(lock_manager):
    CaseReference.objects.create(prefix="bluu", year=None, reference=500)

    ref = allocate_case_reference(
        lock_manager=lock_manager, prefix="bluu", use_year=False, min_digits=2
    )
    assert ref == "bluu/501"


@pytest.mark.django_db
def test_year(lock_manager):
    year = timezone.now().year

    ref1 = allocate_case_reference(
        lock_manager=lock_manager, prefix="blii", use_year=True, min_digits=3
    )
    assert ref1 == f"blii/{year}/001"

    ref2 = allocate_case_reference(
        lock_manager=lock_manager, prefix="blii", use_year=True, min_digits=4
    )
    assert ref2 == f"blii/{year}/0002"


def test_unallocated_application_raises_error(wood_app_in_progress):
    with pytest.raises(ValueError, match="Application has not been assigned yet."):
        get_variation_request_case_reference(wood_app_in_progress)


def test_get_wood_app_variation_request_case_reference(wood_app_submitted, test_icms_admin_user):
    initial_reference = wood_app_submitted.get_reference()
    assert re.match(CASE_REF_PATTERN, initial_reference)

    # Add a variation request
    _add_variation_request(wood_app_submitted, test_icms_admin_user)

    expected_reference = f"{initial_reference}/1"
    actual_reference = get_variation_request_case_reference(wood_app_submitted)

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
    actual_reference = get_variation_request_case_reference(wood_app_submitted)

    assert expected_reference == actual_reference


def test_get_com_app_variation_request_case_reference(com_app_submitted, test_icms_admin_user):
    initial_reference = com_app_submitted.get_reference()
    assert re.match(CASE_REF_PATTERN, initial_reference)

    # Add a variation request
    _add_variation_request(com_app_submitted, test_icms_admin_user)

    expected_reference = f"{initial_reference}/1"
    actual_reference = get_variation_request_case_reference(com_app_submitted)

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
    actual_reference = get_variation_request_case_reference(com_app_submitted)

    assert expected_reference == actual_reference

    # Update the OPEN variation request to CANCELLED.
    open_vr.status = VariationRequest.CANCELLED
    open_vr.save()

    expected_reference = f"{initial_reference}/5"
    actual_reference = get_variation_request_case_reference(com_app_submitted)

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


def _add_variation_request(
    app, user, what_varied="Dummy what_varied", status=VariationRequest.OPEN
) -> VariationRequest:
    return app.variation_requests.create(
        status=status,
        what_varied=what_varied,
        why_varied="Dummy why_varied",
        when_varied=datetime.date.today(),
        requested_by=user,
    )


def test_get_import_application_licence_reference():
    tests = [
        ("electronic", ProcessTypes.DEROGATIONS.value, 1, "GBSAN0000001B"),
        ("electronic", ProcessTypes.FA_DFL.value, 2, "GBSIL0000002C"),
        ("electronic", ProcessTypes.FA_OIL.value, 3, "GBOIL0000003D"),
        ("electronic", ProcessTypes.FA_SIL.value, 4, "GBSIL0000004E"),
        ("electronic", ProcessTypes.IRON_STEEL.value, 5, "GBAOG0000005F"),
        ("electronic", ProcessTypes.SPS.value, 6, "GBAOG0000006G"),
        ("electronic", ProcessTypes.SANCTIONS.value, 7, "GBSAN0000007H"),
        ("electronic", ProcessTypes.TEXTILES.value, 8, "GBTEX0000008X"),
        ("paper", ProcessTypes.DEROGATIONS.value, 9, "0000009J"),
        ("paper", ProcessTypes.FA_DFL.value, 10, "0000010K"),
        ("paper", ProcessTypes.FA_OIL.value, 11, "0000011L"),
        ("paper", ProcessTypes.FA_SIL.value, 12, "0000012M"),
        ("paper", ProcessTypes.IRON_STEEL.value, 13, "0000013A"),
        ("paper", ProcessTypes.SPS.value, 14, "0000014B"),
        ("paper", ProcessTypes.SANCTIONS.value, 15, "0000015C"),
        ("paper", ProcessTypes.TEXTILES.value, 16, "0000016D"),
    ]

    for licence_type, process_type, next_sequence_value, expected_reference in tests:
        actual_reference = get_import_application_licence_reference(
            licence_type, process_type, next_sequence_value
        )

        assert expected_reference == actual_reference, f"Expected failed {expected_reference}"
