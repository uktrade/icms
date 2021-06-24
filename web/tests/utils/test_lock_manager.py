import pytest
from django.db import transaction

from web.models import CaseReference, ExportApplication, ImportApplication
from web.utils.lock_manager import LockManager


@pytest.fixture
def lock_manager():
    return LockManager()


def test_no_tables(lock_manager):
    with pytest.raises(RuntimeError, match="no tables given"):
        lock_manager.lock_tables([])


# TODO: enabling this causes 22 random test failures elsewhere, just setting
# transaction=True somehow modifies global DB state??
#
# @pytest.mark.django_db(transaction=True)
# def test_no_transaction(lock_manager):
#     with pytest.raises(
#         RuntimeError,
#         match="lock_tables cannot be called without being inside a database transaction",
#     ):
#         lock_manager.lock_tables([CaseReference])


@pytest.mark.django_db
def test_success(lock_manager):
    assert not lock_manager.is_table_locked(CaseReference)
    assert not lock_manager.is_table_locked(ImportApplication)
    assert not lock_manager.is_table_locked(ExportApplication)

    with transaction.atomic():
        lock_manager.lock_tables([CaseReference, ImportApplication])

        assert lock_manager.is_table_locked(CaseReference)
        assert lock_manager.is_table_locked(ImportApplication)
        assert not lock_manager.is_table_locked(ExportApplication)


@pytest.mark.django_db
def test_double_lock(lock_manager):
    with transaction.atomic():
        lock_manager.lock_tables([CaseReference])

        with pytest.raises(RuntimeError, match="lock_tables has already been called"):
            lock_manager.lock_tables([CaseReference])


@pytest.mark.django_db
def test_ensure_no_lock_before(lock_manager):
    with transaction.atomic():
        lock_manager.ensure_tables_are_locked([CaseReference])

        assert lock_manager.is_table_locked(CaseReference)


@pytest.mark.django_db
def test_ensure_lock_before_no_extras(lock_manager):
    with transaction.atomic():
        lock_manager.lock_tables([CaseReference])
        lock_manager.ensure_tables_are_locked([CaseReference])

        assert lock_manager.is_table_locked(CaseReference)


@pytest.mark.django_db
def test_ensure_lock_before_yes_extras(lock_manager):
    with transaction.atomic():
        lock_manager.lock_tables([CaseReference])

        with pytest.raises(
            RuntimeError, match="cannot lock extra tables: .'web_importapplication'."
        ):
            lock_manager.ensure_tables_are_locked([CaseReference, ImportApplication])
