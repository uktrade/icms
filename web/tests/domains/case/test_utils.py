import datetime
import re
from unittest.mock import Mock

import pytest
from django.utils import timezone

from web.domains.case.models import VariationRequest
from web.domains.case.utils import (
    allocate_case_reference,
    get_variation_request_case_reference,
)
from web.models.models import CaseReference


@pytest.fixture
def lock_manager():
    return Mock()


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


def test_app_with_no_variation_requests_raises_error(wood_app_submitted):
    with pytest.raises(ValueError, match="Application has no variation requests."):
        get_variation_request_case_reference(wood_app_submitted)


def test_get_variation_request_case_reference(wood_app_submitted, test_icms_admin_user):
    ref_pattern = re.compile(
        r"""
            [a-z]+  # Prefix
            /       # Separator
            \d+     # Year
            /       # Separator
            \d+     # reference
        """,
        flags=re.IGNORECASE | re.VERBOSE,
    )

    initial_reference = wood_app_submitted.get_reference()
    assert re.match(ref_pattern, initial_reference)

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


def _add_variation_request(
    wood_application, user, what_varied="Dummy what_varied", status=VariationRequest.OPEN
):
    wood_application.variation_requests.create(
        status=status,
        what_varied=what_varied,
        why_varied="Dummy why_varied",
        when_varied=datetime.date.today(),
        requested_by=user,
    )
