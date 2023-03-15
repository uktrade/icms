from typing import TYPE_CHECKING

from web.domains.case.services import case_progress
from web.domains.case.types import ImpOrExpOrAccess, ImpOrExpOrAccessT, ImpOrExpT
from web.flow.errors import ProcessError
from web.models import AccessRequest, ExportApplication, ImportApplication

if TYPE_CHECKING:
    from web.models import User


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


def get_caseworker_view_readonly_status(
    application: ImpOrExpOrAccess, case_type: str, user: "User"
) -> bool:
    """For the supplied application work out if the view should be readonly or not.

    This is used for "case management" views.
    """

    try:
        if case_type == "access":
            case_progress.access_request_in_processing(application)
        else:
            case_progress.application_in_processing(application)

        is_case_owner = user == application.case_owner
        is_readonly = not is_case_owner

    except ProcessError:
        is_readonly = True

    return is_readonly
