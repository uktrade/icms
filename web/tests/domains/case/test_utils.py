from unittest.mock import Mock

import pytest
from django.utils import timezone

from web.domains.case.utils import allocate_case_reference
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
