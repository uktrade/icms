import pytest

from web.domains.case._import.models import ImportApplication
from web.domains.case.access.models import AccessRequest
from web.domains.case.export.models import ExportApplication
from web.domains.case.services import case_progress
from web.domains.case.views.utils import (
    get_caseworker_view_readonly_status,
    get_class_imp_or_exp,
    get_class_imp_or_exp_or_access,
)
from web.flow.models import Task
from web.tests.helpers import CaseURLS


def test_get_current_task_and_readonly_status(
    wood_app_submitted, icms_admin_client, test_icms_admin_user, test_import_user
):
    # Test submitted app (no case worker assigned yet) is readonly
    readonly_view = get_caseworker_view_readonly_status(
        wood_app_submitted, "import", test_icms_admin_user
    )
    task = case_progress.get_expected_task(wood_app_submitted, Task.TaskType.PROCESS)
    assert readonly_view
    assert task.task_type == Task.TaskType.PROCESS

    # Now assign case to the case worker.
    icms_admin_client.post(CaseURLS.take_ownership(wood_app_submitted.pk))
    wood_app_submitted.refresh_from_db()

    # Test a submitted app with a case worker (admin user request)
    readonly_view = get_caseworker_view_readonly_status(
        wood_app_submitted, "import", test_icms_admin_user
    )
    task = case_progress.get_expected_task(wood_app_submitted, Task.TaskType.PROCESS)
    assert not readonly_view
    assert task.task_type == Task.TaskType.PROCESS

    # Test a submitted app with a case worker (importer user request)
    readonly_view = get_caseworker_view_readonly_status(
        wood_app_submitted, "import", test_import_user
    )
    task = case_progress.get_expected_task(wood_app_submitted, Task.TaskType.PROCESS)

    assert readonly_view
    assert task.task_type == Task.TaskType.PROCESS


def test_get_current_task_and_readonly_status_in_progress_app(
    wood_app_in_progress, test_icms_admin_user
):
    # Test an in progress app should be readonly
    readonly_view = get_caseworker_view_readonly_status(
        wood_app_in_progress, "import", test_icms_admin_user
    )

    # The task returned above is PREPARE (Which means it's in progress)
    task = case_progress.get_expected_task(wood_app_in_progress, Task.TaskType.PREPARE)

    assert readonly_view
    assert task.task_type == Task.TaskType.PREPARE


@pytest.mark.parametrize(
    "case_type,expected_model",
    [
        ("import", ImportApplication),
        ("export", ExportApplication),
    ],
)
def test_get_class_imp_or_exp(case_type, expected_model):
    actual = get_class_imp_or_exp(case_type)

    assert expected_model == actual


def test_get_class_imp_or_exp_unknown():
    with pytest.raises(NotImplementedError, match="Unknown case_type unknown"):
        get_class_imp_or_exp("unknown")


@pytest.mark.parametrize(
    "case_type,expected_model",
    [
        ("import", ImportApplication),
        ("export", ExportApplication),
        ("access", AccessRequest),
    ],
)
def test_get_class_imp_or_exp_or_access(case_type, expected_model):
    actual = get_class_imp_or_exp_or_access(case_type)

    assert expected_model == actual


def test_get_class_imp_or_exp_or_access_unknown():
    with pytest.raises(NotImplementedError, match="Unknown case_type unknown"):
        get_class_imp_or_exp_or_access("unknown")
