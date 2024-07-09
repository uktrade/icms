import pytest
from django.db import transaction

from web.models import ExportApplication, ImportApplication, UniqueReference
from web.utils.lock_manager import LockManager


@pytest.fixture
def lock_manager():
    return LockManager()


def test_no_tables(lock_manager):
    with pytest.raises(RuntimeError, match="no tables given"):
        lock_manager.lock_tables([])


@pytest.mark.django_db
def test_success(lock_manager):
    assert not lock_manager.is_table_locked(UniqueReference)
    assert not lock_manager.is_table_locked(ImportApplication)
    assert not lock_manager.is_table_locked(ExportApplication)

    with transaction.atomic():
        lock_manager.lock_tables([UniqueReference, ImportApplication])

        assert lock_manager.is_table_locked(UniqueReference)
        assert lock_manager.is_table_locked(ImportApplication)
        assert not lock_manager.is_table_locked(ExportApplication)


@pytest.mark.django_db
def test_double_lock(lock_manager):
    with transaction.atomic():
        lock_manager.lock_tables([UniqueReference])

        with pytest.raises(RuntimeError, match="lock_tables has already been called"):
            lock_manager.lock_tables([UniqueReference])


@pytest.mark.django_db
def test_ensure_no_lock_before(lock_manager):
    with transaction.atomic():
        lock_manager.ensure_tables_are_locked([UniqueReference])

        assert lock_manager.is_table_locked(UniqueReference)


@pytest.mark.django_db
def test_ensure_lock_before_no_extras(lock_manager):
    with transaction.atomic():
        lock_manager.lock_tables([UniqueReference])
        lock_manager.ensure_tables_are_locked([UniqueReference])

        assert lock_manager.is_table_locked(UniqueReference)


@pytest.mark.django_db
def test_ensure_lock_before_yes_extras(lock_manager):
    with transaction.atomic():
        lock_manager.lock_tables([UniqueReference])

        with pytest.raises(
            RuntimeError, match="cannot lock extra tables: .'web_importapplication'."
        ):
            lock_manager.ensure_tables_are_locked([UniqueReference, ImportApplication])
