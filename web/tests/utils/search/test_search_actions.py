import datetime

import pytest

from web.domains.case._import.models import ImportApplication
from web.domains.case._import.wood.models import WoodQuotaApplication
from web.domains.case.export.models import CertificateOfManufactureApplication
from web.utils.search import types
from web.utils.search.api import get_export_record_actions, get_import_record_actions

_st = ImportApplication.Statuses
_future_date = datetime.date(datetime.date.today().year + 1, 1, 1)


test_arg_values = [
    (WoodQuotaApplication(status=_st.IN_PROGRESS), []),
    (WoodQuotaApplication(status=_st.STOPPED), ["Reopen Case"]),
    (WoodQuotaApplication(status=_st.WITHDRAWN), ["Reopen Case"]),
    (WoodQuotaApplication(status=_st.COMPLETED), ["Request Variation"]),
    (
        WoodQuotaApplication(status=_st.COMPLETED, decision=ImportApplication.REFUSE),
        ["Request Variation", "Manage Appeals"],
    ),
    (
        WoodQuotaApplication(status=_st.COMPLETED, licence_end_date=_future_date),
        ["Request Variation", "Revoke Licence"],
    ),
]


@pytest.mark.parametrize(argnames="application, expected_actions", argvalues=test_arg_values)
def test_get_import_application_search_actions(application, expected_actions):
    # get_import_record_actions calls reverse and expects a PK to be set.
    application.pk = 1

    actions: list[types.SearchAction] = get_import_record_actions(application)

    assert expected_actions == [a.label for a in actions]


def test_get_export_application_search_actions():
    app = CertificateOfManufactureApplication()
    actions = get_export_record_actions(app)

    assert actions == []
