import pytest

from web.domains.case.services import case_progress
from web.domains.case.views.utils import (
    get_caseworker_view_readonly_status,
    get_class_imp_or_exp,
    get_class_imp_or_exp_or_access,
)
from web.models import AccessRequest, ExportApplication, ImportApplication, Task
from web.tests.helpers import CaseURLS


def test_get_current_task_and_readonly_status(
    wood_app_submitted, ilb_admin_client, ilb_admin_user, importer_one_contact
):
    # Test submitted app (no case worker assigned yet) is readonly
    readonly_view = get_caseworker_view_readonly_status(
        wood_app_submitted, "import", ilb_admin_user
    )
    case_progress.check_expected_task(wood_app_submitted, Task.TaskType.PROCESS)
    assert readonly_view

    # Now assign case to the case worker.
    ilb_admin_client.post(CaseURLS.take_ownership(wood_app_submitted.pk))
    wood_app_submitted.refresh_from_db()

    # Test a submitted app with a case worker (admin user request)
    readonly_view = get_caseworker_view_readonly_status(
        wood_app_submitted, "import", ilb_admin_user
    )
    case_progress.check_expected_task(wood_app_submitted, Task.TaskType.PROCESS)
    assert not readonly_view

    # Test a submitted app with a case worker (importer user request)
    readonly_view = get_caseworker_view_readonly_status(
        wood_app_submitted, "import", importer_one_contact
    )
    case_progress.check_expected_task(wood_app_submitted, Task.TaskType.PROCESS)

    assert readonly_view


def test_get_current_task_and_readonly_status_in_progress_app(wood_app_in_progress, ilb_admin_user):
    # Test an in progress app should be readonly
    readonly_view = get_caseworker_view_readonly_status(
        wood_app_in_progress, "import", ilb_admin_user
    )

    case_progress.check_expected_task(wood_app_in_progress, Task.TaskType.PREPARE)

    assert readonly_view


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
