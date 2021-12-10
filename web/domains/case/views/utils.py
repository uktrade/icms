from typing import TYPE_CHECKING

from web.domains.case.types import ImpOrExp, ImpOrExpOrAccessT, ImpOrExpT
from web.domains.case.utils import get_application_current_task
from web.flow.errors import ProcessError
from web.models import AccessRequest, ExportApplication, ImportApplication

if TYPE_CHECKING:
    from web.domains.user.models import User
    from web.flow.models import Task


def get_class_imp_or_exp(case_type: str) -> ImpOrExpT:
    if case_type == "import":
        return ImportApplication
    elif case_type == "export":
        return ExportApplication
    else:
        raise NotImplementedError(f"Unknown case_type {case_type}")


def get_class_imp_or_exp_or_access(case_type: str) -> ImpOrExpOrAccessT:
    if case_type == "import":
        return ImportApplication
    elif case_type == "export":
        return ExportApplication
    elif case_type == "access":
        return AccessRequest
    else:
        raise NotImplementedError(f"Unknown case_type {case_type}")


def get_current_task_and_readonly_status(
    application: ImpOrExp,
    case_type: str,
    user: "User",
    task_type: str,
    select_for_update: bool = True,
) -> tuple["Task", bool]:
    """For the supplied application work out if the view should be readonly or not.

    This is used for "case management" views.
    """

    try:
        task = get_application_current_task(
            application, case_type, task_type, select_for_update=select_for_update
        )
        is_case_owner = user == application.case_owner
        is_readonly = not is_case_owner

    except ProcessError:
        task = application.get_active_task()  # type: ignore[assignment]
        is_readonly = True

    return task, is_readonly
