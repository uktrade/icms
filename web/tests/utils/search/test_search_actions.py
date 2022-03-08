import datetime

import pytest

from web.domains.case._import.models import ImportApplication, ImportApplicationLicence
from web.domains.case._import.wood.models import WoodQuotaApplication
from web.domains.case.export.models import CertificateOfManufactureApplication
from web.domains.case.shared import ImpExpStatus
from web.utils.search import types
from web.utils.search.api import get_export_record_actions, get_import_record_actions

_st = ImpExpStatus
_future_date = datetime.date(datetime.date.today().year + 1, 1, 1)
_past_date = datetime.date(datetime.date.today().year - 1, 1, 1)


test_import_arg_values = [
    (WoodQuotaApplication(status=_st.IN_PROGRESS), ImportApplicationLicence(), []),
    (WoodQuotaApplication(status=_st.STOPPED), ImportApplicationLicence(), ["Reopen Case"]),
    (WoodQuotaApplication(status=_st.WITHDRAWN), ImportApplicationLicence(), ["Reopen Case"]),
    (
        WoodQuotaApplication(status=_st.COMPLETED),
        ImportApplicationLicence(licence_end_date=_future_date),
        ["Request Variation", "Revoke Licence"],
    ),
    (
        WoodQuotaApplication(status=_st.COMPLETED, decision=ImportApplication.REFUSE),
        ImportApplicationLicence(licence_end_date=_future_date),
        ["Request Variation", "Manage Appeals", "Revoke Licence"],
    ),
    (
        WoodQuotaApplication(status=_st.COMPLETED),
        ImportApplicationLicence(licence_end_date=_past_date),
        [],
    ),
]


@pytest.mark.parametrize(
    argnames="application, licence, expected_actions", argvalues=test_import_arg_values
)
def test_get_import_application_search_actions(
    application, licence, expected_actions, test_icms_admin_user
):
    # get_import_record_actions calls reverse and expects a PK to be set.
    application.pk = 1
    # TODO: ICMSLST-1240 Add permission tests
    user = test_icms_admin_user

    # Add a fake annotation to the application record.
    application.latest_licence_end_date = licence.licence_end_date
    actions: list[types.SearchAction] = get_import_record_actions(application, user)

    assert expected_actions == [a.label for a in actions]


test_export_arg_values = [
    (CertificateOfManufactureApplication(status=_st.STOPPED), ["Reopen Case"]),
    (CertificateOfManufactureApplication(status=_st.WITHDRAWN), ["Reopen Case"]),
    (
        CertificateOfManufactureApplication(status=_st.IN_PROGRESS),
        ["Copy Application", "Create Template"],
    ),
    (
        CertificateOfManufactureApplication(status=_st.COMPLETED),
        ["Open Variation", "Revoke Certificates", "Copy Application", "Create Template"],
    ),
]


@pytest.mark.parametrize(argnames="application, expected_actions", argvalues=test_export_arg_values)
def test_get_export_application_search_actions(application, expected_actions, test_icms_admin_user):
    # get_export_record_actions calls reverse and expects a PK to be set.
    application.pk = 1
    # TODO: ICMSLST-1240 Add permission tests
    user = test_icms_admin_user

    actions = get_export_record_actions(application, user)

    assert expected_actions == [a.label for a in actions]
