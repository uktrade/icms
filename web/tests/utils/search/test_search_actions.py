import datetime

import pytest

from web.domains.case._import.models import ImportApplication
from web.domains.case._import.wood.models import WoodQuotaApplication
from web.domains.case.export.models import (
    CertificateOfManufactureApplication,
    ExportApplication,
)
from web.utils.search import types
from web.utils.search.api import get_export_record_actions, get_import_record_actions

_ist = ImportApplication.Statuses
_ext = ExportApplication.Statuses
_future_date = datetime.date(datetime.date.today().year + 1, 1, 1)


test_import_arg_values = [
    (WoodQuotaApplication(status=_ist.IN_PROGRESS), []),
    (WoodQuotaApplication(status=_ist.STOPPED), ["Reopen Case"]),
    (WoodQuotaApplication(status=_ist.WITHDRAWN), ["Reopen Case"]),
    (WoodQuotaApplication(status=_ist.COMPLETED), ["Request Variation"]),
    (
        WoodQuotaApplication(status=_ist.COMPLETED, decision=ImportApplication.REFUSE),
        ["Request Variation", "Manage Appeals"],
    ),
    (
        WoodQuotaApplication(status=_ist.COMPLETED, licence_end_date=_future_date),
        ["Request Variation", "Revoke Licence"],
    ),
]


@pytest.mark.parametrize(argnames="application, expected_actions", argvalues=test_import_arg_values)
def test_get_import_application_search_actions(application, expected_actions):
    # get_import_record_actions calls reverse and expects a PK to be set.
    application.pk = 1
    # TODO: ICMSLST-1240 Add permission tests
    user = None

    actions: list[types.SearchAction] = get_import_record_actions(application, user)

    assert expected_actions == [a.label for a in actions]


test_export_arg_values = [
    (CertificateOfManufactureApplication(status=_ext.STOPPED), ["Reopen Case"]),
    (CertificateOfManufactureApplication(status=_ext.WITHDRAWN), ["Reopen Case"]),
    (
        CertificateOfManufactureApplication(status=_ext.IN_PROGRESS),
        ["Copy Application", "Create Template"],
    ),
    (
        CertificateOfManufactureApplication(status=_ext.COMPLETED),
        ["Open Variation", "Revoke Certificates", "Copy Application", "Create Template"],
    ),
]


@pytest.mark.parametrize(argnames="application, expected_actions", argvalues=test_export_arg_values)
def test_get_export_application_search_actions(application, expected_actions):
    # get_export_record_actions calls reverse and expects a PK to be set.
    application.pk = 1
    # TODO: ICMSLST-1240 Add permission tests
    user = None

    actions = get_export_record_actions(application, user)

    assert expected_actions == [a.label for a in actions]
