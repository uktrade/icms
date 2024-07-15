import datetime as dt
from typing import Any
from unittest.mock import patch

import freezegun
import pytest
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone
from guardian.shortcuts import remove_perm

from web.domains.case.tasks import create_document_pack_on_success
from web.domains.workbasket.base import WorkbasketRow
from web.forms.fields import JQUERY_DATE_FORMAT
from web.models import (
    AccessRequest,
    ApprovalRequest,
    Exporter,
    ExporterAccessRequest,
    FurtherInformationRequest,
    ImportApplication,
    Importer,
    ImporterAccessRequest,
    Mailshot,
    Template,
    User,
)
from web.models.shared import YesNoNAChoices
from web.permissions import Perms
from web.tests.auth.auth import AuthTestCase
from web.tests.helpers import CaseURLS, add_approval_request, get_linked_access_request


class TestApplicationInProgressWorkbasket(AuthTestCase):
    """Test workbasket rows where each case is in progress."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        _setup,
        fa_dfl_app_in_progress,
        fa_dfl_agent_app_in_progress,
        com_app_in_progress,
        com_agent_app_in_progress,
    ):
        self.imp_app = fa_dfl_app_in_progress
        self.imp_agent_app = fa_dfl_agent_app_in_progress
        self.exp_app = com_app_in_progress
        self.exp_agent_app = com_agent_app_in_progress

        _fix_access_request_data()

    def test_workbasket(self):
        self._test_ilb_admin_wb()
        self._test_importer_contact_wb()
        self._test_importer_agent_wb()
        self._test_exporter_contact_wb()
        self._test_exporter_agent_wb()

    def _test_ilb_admin_wb(self):
        expected_rows = {}
        check_expected_rows(self.ilb_admin_client, expected_rows)

    def _test_importer_contact_wb(self):
        expected_rows = {
            # self.imp_app.reference == "Not Assigned"
            "Not Assigned": {"In Progress": {"Prepare Application": ["Resume", "Cancel"]}}
        }

        check_expected_rows(self.importer_client, expected_rows)

        _remove_edit_permission(self.importer_user, self.imp_app.importer)
        expected_rows = {"Not Assigned": {"In Progress": {}}}
        check_expected_rows(self.importer_client, expected_rows)

    def _test_importer_agent_wb(self):
        expected_rows = {
            # self.imp_agent_app.reference == "Not Assigned"
            "Not Assigned": {"In Progress": {"Prepare Application": ["Resume", "Cancel"]}}
        }

        check_expected_rows(self.importer_agent_client, expected_rows)

        _remove_edit_permission(self.importer_agent_user, self.imp_agent_app.agent)
        expected_rows = {"Not Assigned": {"In Progress": {}}}
        check_expected_rows(self.importer_agent_client, expected_rows)

    def _test_exporter_contact_wb(self):
        expected_rows = {
            # self.exp_app.reference == "Not Assigned"
            "Not Assigned": {"In Progress": {"Prepare Application": ["Resume", "Cancel"]}}
        }

        check_expected_rows(self.exporter_client, expected_rows)

        _remove_edit_permission(self.exporter_user, self.exp_app.exporter)
        expected_rows = {"Not Assigned": {"In Progress": {}}}
        check_expected_rows(self.exporter_client, expected_rows)

    def _test_exporter_agent_wb(self):
        expected_rows = {
            # self.exp_agent_app.reference == "Not Assigned"
            "Not Assigned": {"In Progress": {"Prepare Application": ["Resume", "Cancel"]}}
        }

        check_expected_rows(self.exporter_agent_client, expected_rows)

        _remove_edit_permission(self.exporter_agent_user, self.exp_agent_app.agent)
        expected_rows = {"Not Assigned": {"In Progress": {}}}
        check_expected_rows(self.exporter_agent_client, expected_rows)


class TestApplicationSubmittedWorkbasket(AuthTestCase):
    """Test workbasket rows where each case has been submitted."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        _setup,
        fa_dfl_app_submitted,
        fa_dfl_agent_app_submitted,
        com_app_submitted,
        com_agent_app_submitted,
    ):
        self.imp_app = fa_dfl_app_submitted
        self.imp_agent_app = fa_dfl_agent_app_submitted
        self.exp_app = com_app_submitted
        self.exp_agent_app = com_agent_app_submitted

        _fix_access_request_data()

    def test_workbasket(self):
        self._test_ilb_admin_wb()
        self._test_importer_contact_wb()
        self._test_importer_agent_wb()
        self._test_exporter_contact_wb()
        self._test_exporter_agent_wb()

    def _test_ilb_admin_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Submitted": {"Application Processing": ["Take Ownership", "View"]}
            },
            self.imp_agent_app.reference: {
                "Submitted": {"Application Processing": ["Take Ownership", "View"]}
            },
            self.exp_app.reference: {
                "Submitted": {"Application Processing": ["Take Ownership", "View"]}
            },
            self.exp_agent_app.reference: {
                "Submitted": {"Application Processing": ["Take Ownership", "View"]}
            },
        }
        check_expected_rows(self.ilb_admin_client, expected_rows)

    def _test_importer_contact_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Submitted": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.importer_client, expected_rows)

        _remove_edit_permission(self.importer_user, self.imp_app.importer)
        expected_rows = {
            self.imp_app.reference: {"Submitted": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.importer_client, expected_rows)

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Submitted": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.importer_agent_client, expected_rows)

        _remove_edit_permission(self.importer_agent_user, self.imp_agent_app.agent)
        expected_rows = {
            self.imp_agent_app.reference: {
                "Submitted": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.importer_agent_client, expected_rows)

    def _test_exporter_contact_wb(self):
        expected_rows = {
            self.exp_app.reference: {
                "Submitted": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.exporter_client, expected_rows)

        _remove_edit_permission(self.exporter_user, self.exp_app.exporter)
        expected_rows = {
            self.exp_app.reference: {"Submitted": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.exporter_client, expected_rows)

    def _test_exporter_agent_wb(self):
        expected_rows = {
            self.exp_agent_app.reference: {
                "Submitted": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.exporter_agent_client, expected_rows)

        _remove_edit_permission(self.exporter_agent_user, self.exp_agent_app.agent)
        expected_rows = {
            self.exp_agent_app.reference: {
                "Submitted": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.exporter_agent_client, expected_rows)


class TestApplicationManagedWorkbasket(AuthTestCase):
    """Test workbasket rows where each case is being managed by a case officer."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        _setup,
        fa_dfl_app_submitted,
        fa_dfl_agent_app_submitted,
        com_app_submitted,
        com_agent_app_submitted,
    ):
        self.imp_app = fa_dfl_app_submitted
        self.imp_agent_app = fa_dfl_agent_app_submitted
        self.exp_app = com_app_submitted
        self.exp_agent_app = com_agent_app_submitted

        _fix_access_request_data()

        # Take ownership of cases (two case officers)
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_app.pk, "import"))
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_agent_app.pk, "import"))
        self.ilb_admin_two_client.post(CaseURLS.take_ownership(self.exp_app.pk, "export"))
        self.ilb_admin_two_client.post(CaseURLS.take_ownership(self.exp_agent_app.pk, "export"))

    def test_workbasket(self):
        self._test_ilb_admin_wb()
        self._test_importer_contact_wb()
        self._test_importer_agent_wb()
        self._test_exporter_contact_wb()
        self._test_exporter_agent_wb()

    def _test_ilb_admin_wb(self):
        expected_rows = {
            self.imp_app.reference: {"Processing": {"Application Processing": ["Manage"]}},
            self.imp_agent_app.reference: {"Processing": {"Application Processing": ["Manage"]}},
        }
        check_expected_rows(self.ilb_admin_client, expected_rows)

        expected_rows = {
            self.exp_app.reference: {"Processing": {"Application Processing": ["Manage"]}},
            self.exp_agent_app.reference: {"Processing": {"Application Processing": ["Manage"]}},
        }
        check_expected_rows(self.ilb_admin_two_client, expected_rows)

    def _test_importer_contact_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.importer_client, expected_rows)

        _remove_edit_permission(self.importer_user, self.imp_app.importer)
        expected_rows = {
            self.imp_app.reference: {"Processing": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.importer_client, expected_rows)

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.importer_agent_client, expected_rows)

        _remove_edit_permission(self.importer_agent_user, self.imp_agent_app.agent)
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.importer_agent_client, expected_rows)

    def _test_exporter_contact_wb(self):
        expected_rows = {
            self.exp_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.exporter_client, expected_rows)

        _remove_edit_permission(self.exporter_user, self.exp_app.exporter)
        expected_rows = {
            self.exp_app.reference: {"Processing": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.exporter_client, expected_rows)

    def _test_exporter_agent_wb(self):
        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.exporter_agent_client, expected_rows)

        _remove_edit_permission(self.exporter_agent_user, self.exp_agent_app.agent)
        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.exporter_agent_client, expected_rows)


class TestApplicationWithdrawalWorkbasket(AuthTestCase):
    """Test workbasket rows where each case has an open withdrawal request."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        _setup,
        fa_dfl_app_submitted,
        fa_dfl_agent_app_submitted,
        com_app_submitted,
        com_agent_app_submitted,
    ):
        self.imp_app = fa_dfl_app_submitted
        self.imp_agent_app = fa_dfl_agent_app_submitted
        self.exp_app = com_app_submitted
        self.exp_agent_app = com_agent_app_submitted

        _fix_access_request_data()

        # Take ownership of a few cases (different actions if not owned)
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_app.pk, "import"))
        self.ilb_admin_two_client.post(CaseURLS.take_ownership(self.exp_agent_app.pk, "export"))

        # Withdraw each app
        form_data = {"reason": "Test withdrawal"}
        self.importer_client.post(
            CaseURLS.withdrawal_case(self.imp_app.pk, "import"), data=form_data
        )
        self.importer_agent_client.post(
            CaseURLS.withdrawal_case(self.imp_agent_app.pk, "import"), data=form_data
        )
        self.exporter_client.post(
            CaseURLS.withdrawal_case(self.exp_app.pk, "export"), data=form_data
        )
        self.exporter_agent_client.post(
            CaseURLS.withdrawal_case(self.exp_agent_app.pk, "export"), data=form_data
        )

    def test_workbasket(self):
        self._test_ilb_admin_wb()
        self._test_importer_contact_wb()
        self._test_importer_agent_wb()
        self._test_exporter_contact_wb()
        self._test_exporter_agent_wb()

    def _test_ilb_admin_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Processing": {
                    "Application Processing": ["Manage"],
                    "Withdraw Pending": ["Withdrawal Request"],
                }
            },
            self.imp_agent_app.reference: {
                "Submitted": {
                    "Application Processing": ["Take Ownership", "View"],
                    "Withdraw Pending": ["View Withdrawal Request"],
                }
            },
            self.exp_app.reference: {
                "Submitted": {
                    "Application Processing": ["Take Ownership", "View"],
                    "Withdraw Pending": ["View Withdrawal Request"],
                }
            },
        }
        check_expected_rows(self.ilb_admin_client, expected_rows)

        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {
                    "Application Processing": ["Manage"],
                    "Withdraw Pending": ["Withdrawal Request"],
                }
            },
            self.imp_agent_app.reference: {
                "Submitted": {
                    "Application Processing": ["Take Ownership", "View"],
                    "Withdraw Pending": ["View Withdrawal Request"],
                }
            },
            self.exp_app.reference: {
                "Submitted": {
                    "Application Processing": ["Take Ownership", "View"],
                    "Withdraw Pending": ["View Withdrawal Request"],
                }
            },
        }
        check_expected_rows(self.ilb_admin_two_client, expected_rows)

    def _test_importer_contact_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Processing": {"Application Submitted": ["Pending Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.importer_client, expected_rows)

        _remove_edit_permission(self.importer_user, self.imp_app.importer)
        expected_rows = {
            self.imp_app.reference: {"Processing": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.importer_client, expected_rows)

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Submitted": {"Application Submitted": ["Pending Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.importer_agent_client, expected_rows)

        _remove_edit_permission(self.importer_agent_user, self.imp_agent_app.agent)
        expected_rows = {
            self.imp_agent_app.reference: {
                "Submitted": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.importer_agent_client, expected_rows)

    def _test_exporter_contact_wb(self):
        expected_rows = {
            self.exp_app.reference: {
                "Submitted": {"Application Submitted": ["Pending Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.exporter_client, expected_rows)

        _remove_edit_permission(self.exporter_user, self.exp_app.exporter)
        expected_rows = {
            self.exp_app.reference: {"Submitted": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.exporter_client, expected_rows)

    def _test_exporter_agent_wb(self):
        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Pending Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.exporter_agent_client, expected_rows)

        _remove_edit_permission(self.exporter_agent_user, self.exp_agent_app.agent)
        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.exporter_agent_client, expected_rows)


class TestApplicationFurtherInformationRequestedWorkbasket(AuthTestCase):
    """Test workbasket rows where each case has an open further information request."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        _setup,
        fa_dfl_app_submitted,
        fa_dfl_agent_app_submitted,
        com_app_submitted,
        com_agent_app_submitted,
    ):
        self.imp_app = fa_dfl_app_submitted
        self.imp_agent_app = fa_dfl_agent_app_submitted
        self.exp_app = com_app_submitted
        self.exp_agent_app = com_agent_app_submitted

        _fix_access_request_data()

        # Take ownership of cases (two case officers)
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_app.pk, "import"))
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_agent_app.pk, "import"))
        self.ilb_admin_two_client.post(CaseURLS.take_ownership(self.exp_app.pk, "export"))
        self.ilb_admin_two_client.post(CaseURLS.take_ownership(self.exp_agent_app.pk, "export"))

        # Create FIR for each app.
        for client, app in (
            (self.ilb_admin_client, self.imp_app),
            (self.ilb_admin_client, self.imp_agent_app),
            (self.ilb_admin_two_client, self.exp_app),
            (self.ilb_admin_two_client, self.exp_agent_app),
        ):
            case_type = "import" if app.is_import_application() else "export"

            with freezegun.freeze_time("2023-07-26 06:38:16"):
                resp = client.post(CaseURLS.add_fir(app.pk, case_type))
                client.post(
                    resp.url,
                    data={
                        "status": "DRAFT",
                        "request_subject": "Test Subject",
                        "request_detail": "Test request detail",
                        "send": "1",
                    },
                )

    def test_workbasket(self):
        self._test_ilb_admin_wb()
        self._test_importer_contact_wb()
        self._test_importer_agent_wb()
        self._test_exporter_contact_wb()
        self._test_exporter_agent_wb()

    def _test_ilb_admin_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Processing": {"Application Processing, Further Information Requested": ["Manage"]}
            },
            self.imp_agent_app.reference: {
                "Processing": {"Application Processing, Further Information Requested": ["Manage"]}
            },
        }
        check_expected_rows(self.ilb_admin_client, expected_rows)

        expected_rows = {
            self.exp_app.reference: {
                "Processing": {"Application Processing, Further Information Requested": ["Manage"]}
            },
            self.exp_agent_app.reference: {
                "Processing": {"Application Processing, Further Information Requested": ["Manage"]}
            },
        }
        check_expected_rows(self.ilb_admin_two_client, expected_rows)

    def _test_importer_contact_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Processing": {
                    "Application Submitted": ["Request Withdrawal", "View Application"],
                    "Further Information Request, 26 Jul 2023 06:38:16": ["Respond"],
                }
            }
        }

        check_expected_rows(self.importer_client, expected_rows)

        _remove_edit_permission(self.importer_user, self.imp_app.importer)
        expected_rows = {
            self.imp_app.reference: {"Processing": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.importer_client, expected_rows)

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {
                    "Application Submitted": ["Request Withdrawal", "View Application"],
                    "Further Information Request, 26 Jul 2023 06:38:16": ["Respond"],
                }
            }
        }

        check_expected_rows(self.importer_agent_client, expected_rows)

        _remove_edit_permission(self.importer_agent_user, self.imp_agent_app.agent)
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.importer_agent_client, expected_rows)

    def _test_exporter_contact_wb(self):
        expected_rows = {
            self.exp_app.reference: {
                "Processing": {
                    "Application Submitted": ["Request Withdrawal", "View Application"],
                    "Further Information Request, 26 Jul 2023 06:38:16": ["Respond"],
                }
            }
        }

        check_expected_rows(self.exporter_client, expected_rows)

        _remove_edit_permission(self.exporter_user, self.exp_app.exporter)
        expected_rows = {
            self.exp_app.reference: {"Processing": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.exporter_client, expected_rows)

    def _test_exporter_agent_wb(self):
        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {
                    "Application Submitted": ["Request Withdrawal", "View Application"],
                    "Further Information Request, 26 Jul 2023 06:38:16": ["Respond"],
                }
            }
        }

        check_expected_rows(self.exporter_agent_client, expected_rows)

        _remove_edit_permission(self.exporter_agent_user, self.exp_agent_app.agent)
        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.exporter_agent_client, expected_rows)


class TestApplicationUpdatesWorkbasket(AuthTestCase):
    """Test workbasket rows where each case has an open application update request."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        _setup,
        fa_dfl_app_submitted,
        fa_dfl_agent_app_submitted,
        com_app_submitted,
        com_agent_app_submitted,
    ):
        self.imp_app = fa_dfl_app_submitted
        self.imp_agent_app = fa_dfl_agent_app_submitted
        self.exp_app = com_app_submitted
        self.exp_agent_app = com_agent_app_submitted

        _fix_access_request_data()

        # Take ownership of cases (two case officers)
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_app.pk, "import"))
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_agent_app.pk, "import"))
        self.ilb_admin_two_client.post(CaseURLS.take_ownership(self.exp_app.pk, "export"))
        self.ilb_admin_two_client.post(CaseURLS.take_ownership(self.exp_agent_app.pk, "export"))

        # Create Application Update Request for each app.
        form_data = {"request_subject": "subject", "request_detail": "detail"}
        self.ilb_admin_client.post(
            CaseURLS.manage_update_requests(self.imp_app.pk, "import"), data=form_data
        )
        self.ilb_admin_client.post(
            CaseURLS.manage_update_requests(self.imp_agent_app.pk, "import"), data=form_data
        )
        self.ilb_admin_two_client.post(
            CaseURLS.manage_update_requests(self.exp_app.pk, "export"), data=form_data
        )
        self.ilb_admin_two_client.post(
            CaseURLS.manage_update_requests(self.exp_agent_app.pk, "export"), data=form_data
        )

        # Start changes on several of them (shows different actions)
        ur_pk = self.imp_app.update_requests.first().pk
        self.importer_client.post(CaseURLS.start_update_request(self.imp_app.pk, ur_pk, "import"))

        ur_pk = self.exp_agent_app.update_requests.first().pk
        self.exporter_agent_client.post(
            CaseURLS.start_update_request(self.exp_agent_app.pk, ur_pk, "export")
        )

        CaseURLS.start_update_request(application_pk=1, update_request_pk=1, case_type="import")

    def test_workbasket(self):
        self._test_ilb_admin_wb()
        self._test_importer_contact_wb()
        self._test_importer_agent_wb()
        self._test_exporter_contact_wb()
        self._test_exporter_agent_wb()

    def _test_ilb_admin_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Processing": {"Application Processing, Out for Update": ["Manage"]}
            },
            self.imp_agent_app.reference: {
                "Processing": {"Application Processing, Out for Update": ["Manage"]}
            },
        }
        check_expected_rows(self.ilb_admin_client, expected_rows)

        expected_rows = {
            self.exp_app.reference: {
                "Processing": {"Application Processing, Out for Update": ["Manage"]}
            },
            self.exp_agent_app.reference: {
                "Processing": {"Application Processing, Out for Update": ["Manage"]}
            },
        }
        check_expected_rows(self.ilb_admin_two_client, expected_rows)

    def _test_importer_contact_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Processing": {
                    "Application Submitted": ["Request Withdrawal", "View Application"],
                    "Application Update in Progress": ["Resume Update"],
                }
            }
        }

        check_expected_rows(self.importer_client, expected_rows)

        _remove_edit_permission(self.importer_user, self.imp_app.importer)
        expected_rows = {
            self.imp_app.reference: {"Processing": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.importer_client, expected_rows)

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {
                    "Application Submitted": ["Request Withdrawal", "View Application"],
                    "Application Update Requested": ["Respond to Update Request"],
                }
            }
        }

        check_expected_rows(self.importer_agent_client, expected_rows)

        _remove_edit_permission(self.importer_agent_user, self.imp_agent_app.agent)
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.importer_agent_client, expected_rows)

    def _test_exporter_contact_wb(self):
        expected_rows = {
            self.exp_app.reference: {
                "Processing": {
                    "Application Submitted": ["Request Withdrawal", "View Application"],
                    "Application Update Requested": ["Respond to Update Request"],
                }
            }
        }

        check_expected_rows(self.exporter_client, expected_rows)

        _remove_edit_permission(self.exporter_user, self.exp_app.exporter)
        expected_rows = {
            self.exp_app.reference: {"Processing": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.exporter_client, expected_rows)

    def _test_exporter_agent_wb(self):
        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {
                    "Application Submitted": ["Request Withdrawal", "View Application"],
                    "Application Update in Progress": ["Resume Update"],
                }
            }
        }

        check_expected_rows(self.exporter_agent_client, expected_rows)

        _remove_edit_permission(self.exporter_agent_user, self.exp_agent_app.agent)
        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.exporter_agent_client, expected_rows)


class TestAuthorisedCaseWorkbasket(AuthTestCase):
    """Test workbasket rows where each case has been authorised by a case officer."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        _setup,
        fa_dfl_app_submitted,
        fa_dfl_agent_app_submitted,
        com_app_submitted,
        com_agent_app_submitted,
    ):
        self.imp_app = fa_dfl_app_submitted
        self.imp_agent_app = fa_dfl_agent_app_submitted
        self.exp_app = com_app_submitted
        self.exp_agent_app = com_agent_app_submitted

        _fix_access_request_data()

        # Take ownership of cases (two case officers)
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_app.pk, "import"))
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_agent_app.pk, "import"))
        self.ilb_admin_two_client.post(CaseURLS.take_ownership(self.exp_app.pk, "export"))
        self.ilb_admin_two_client.post(CaseURLS.take_ownership(self.exp_agent_app.pk, "export"))

        #
        # Complete checklists (import only)
        data = fa_dfl_checklist_form_data()
        self.ilb_admin_client.post(
            reverse("import:fa-dfl:manage-checklist", kwargs={"application_pk": self.imp_app.pk}),
            data=data,
        )
        self.ilb_admin_client.post(
            reverse(
                "import:fa-dfl:manage-checklist", kwargs={"application_pk": self.imp_agent_app.pk}
            ),
            data=data,
        )

        #
        # Complete response prep screen
        form_data = {"decision": ImportApplication.APPROVE}
        self.ilb_admin_client.post(
            CaseURLS.prepare_response(self.imp_app.pk, "import"), data=form_data
        )
        self.ilb_admin_client.post(
            CaseURLS.prepare_response(self.imp_agent_app.pk, "import"), data=form_data
        )
        self.ilb_admin_two_client.post(
            CaseURLS.prepare_response(self.exp_app.pk, "export"), data=form_data
        )
        self.ilb_admin_two_client.post(
            CaseURLS.prepare_response(self.exp_agent_app.pk, "export"), data=form_data
        )

        #
        # Set licence details (import only)
        start_date = dt.date.today()
        end_date = dt.date(start_date.year + 3, 1, 1)
        form_data = {
            "licence_start_date": start_date.strftime(JQUERY_DATE_FORMAT),
            "licence_end_date": end_date.strftime(JQUERY_DATE_FORMAT),
            "issue_paper_licence_only": False,
        }
        self.ilb_admin_client.post(
            reverse("import:edit-licence", kwargs={"application_pk": self.imp_app.pk}),
            data=form_data,
        )
        self.ilb_admin_client.post(
            reverse("import:edit-licence", kwargs={"application_pk": self.imp_agent_app.pk}),
            data=form_data,
        )

        #
        # Start authorisation
        self.ilb_admin_client.post(CaseURLS.start_authorisation(self.imp_app.pk, "import"))
        self.ilb_admin_client.post(CaseURLS.start_authorisation(self.imp_agent_app.pk, "import"))
        self.ilb_admin_two_client.post(CaseURLS.start_authorisation(self.exp_app.pk, "export"))
        self.ilb_admin_two_client.post(
            CaseURLS.start_authorisation(self.exp_agent_app.pk, "export")
        )

    def test_workbasket(self):
        self._test_ilb_admin_wb()
        self._test_importer_contact_wb()
        self._test_importer_agent_wb()
        self._test_exporter_contact_wb()
        self._test_exporter_agent_wb()

    def _test_ilb_admin_wb(self):
        expected_actions = ["Authorise Documents", "Cancel Authorisation", "View Case"]

        expected_rows = {
            self.imp_app.reference: {"Processing": {"Authorise Documents": expected_actions}},
            self.imp_agent_app.reference: {"Processing": {"Authorise Documents": expected_actions}},
        }
        check_expected_rows(self.ilb_admin_client, expected_rows)

        expected_rows = {
            self.exp_app.reference: {"Processing": {"Authorise Documents": expected_actions}},
            self.exp_agent_app.reference: {"Processing": {"Authorise Documents": expected_actions}},
        }
        check_expected_rows(self.ilb_admin_two_client, expected_rows)

    def _test_importer_contact_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.importer_client, expected_rows)

        _remove_edit_permission(self.importer_user, self.imp_app.importer)
        expected_rows = {
            self.imp_app.reference: {"Processing": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.importer_client, expected_rows)

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.importer_agent_client, expected_rows)

        _remove_edit_permission(self.importer_agent_user, self.imp_agent_app.agent)
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.importer_agent_client, expected_rows)

    def _test_exporter_contact_wb(self):
        expected_rows = {
            self.exp_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.exporter_client, expected_rows)

        _remove_edit_permission(self.exporter_user, self.exp_app.exporter)
        expected_rows = {
            self.exp_app.reference: {"Processing": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.exporter_client, expected_rows)

    def _test_exporter_agent_wb(self):
        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.exporter_agent_client, expected_rows)

        _remove_edit_permission(self.exporter_agent_user, self.exp_agent_app.agent)
        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.exporter_agent_client, expected_rows)


class TestAuthorisedCaseAndDocumentsWorkbasket(AuthTestCase):
    """Test workbasket rows where each case has documents signed by a case officer."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        _setup,
        fa_dfl_app_submitted,
        fa_dfl_agent_app_submitted,
        com_app_submitted,
        com_agent_app_submitted,
    ):
        self.imp_app = fa_dfl_app_submitted
        self.imp_agent_app = fa_dfl_agent_app_submitted
        self.exp_app = com_app_submitted
        self.exp_agent_app = com_agent_app_submitted

        _fix_access_request_data()

        # Take ownership of cases (two case officers)
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_app.pk, "import"))
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_agent_app.pk, "import"))
        self.ilb_admin_two_client.post(CaseURLS.take_ownership(self.exp_app.pk, "export"))
        self.ilb_admin_two_client.post(CaseURLS.take_ownership(self.exp_agent_app.pk, "export"))

        #
        # Complete checklists (import only)
        data = fa_dfl_checklist_form_data()
        self.ilb_admin_client.post(
            reverse("import:fa-dfl:manage-checklist", kwargs={"application_pk": self.imp_app.pk}),
            data=data,
        )
        self.ilb_admin_client.post(
            reverse(
                "import:fa-dfl:manage-checklist", kwargs={"application_pk": self.imp_agent_app.pk}
            ),
            data=data,
        )

        #
        # Complete response prep screen
        form_data = {"decision": ImportApplication.APPROVE}
        self.ilb_admin_client.post(
            CaseURLS.prepare_response(self.imp_app.pk, "import"), data=form_data
        )
        self.ilb_admin_client.post(
            CaseURLS.prepare_response(self.imp_agent_app.pk, "import"), data=form_data
        )
        self.ilb_admin_two_client.post(
            CaseURLS.prepare_response(self.exp_app.pk, "export"), data=form_data
        )
        self.ilb_admin_two_client.post(
            CaseURLS.prepare_response(self.exp_agent_app.pk, "export"), data=form_data
        )

        #
        # Set licence details (import only)
        start_date = dt.date.today()
        end_date = dt.date(start_date.year + 3, 1, 1)
        form_data = {
            "licence_start_date": start_date.strftime(JQUERY_DATE_FORMAT),
            "licence_end_date": end_date.strftime(JQUERY_DATE_FORMAT),
            "issue_paper_licence_only": False,
        }
        self.ilb_admin_client.post(
            reverse("import:edit-licence", kwargs={"application_pk": self.imp_app.pk}),
            data=form_data,
        )
        self.ilb_admin_client.post(
            reverse("import:edit-licence", kwargs={"application_pk": self.imp_agent_app.pk}),
            data=form_data,
        )

        #
        # Start authorisation
        self.ilb_admin_client.post(CaseURLS.start_authorisation(self.imp_app.pk, "import"))
        self.ilb_admin_client.post(CaseURLS.start_authorisation(self.imp_agent_app.pk, "import"))
        self.ilb_admin_two_client.post(CaseURLS.start_authorisation(self.exp_app.pk, "export"))
        self.ilb_admin_two_client.post(
            CaseURLS.start_authorisation(self.exp_agent_app.pk, "export")
        )

        #
        # Authorise Documents
        with patch("web.domains.case.views.views_misc.create_case_document_pack", autospec=True):
            form_data = {"password": "test"}
            self.ilb_admin_client.post(
                CaseURLS.authorise_documents(self.imp_app.pk, "import"), data=form_data
            )
            self.ilb_admin_client.post(
                CaseURLS.authorise_documents(self.imp_agent_app.pk, "import"), data=form_data
            )
            self.ilb_admin_two_client.post(
                CaseURLS.authorise_documents(self.exp_app.pk, "export"), data=form_data
            )
            self.ilb_admin_two_client.post(
                CaseURLS.authorise_documents(self.exp_agent_app.pk, "export"), data=form_data
            )

        with freezegun.freeze_time("2023-07-27 10:06:00"):
            # Manually call success task as we've faked creating the documents.
            create_document_pack_on_success(self.imp_app.pk, self.ilb_admin_user.pk)
            create_document_pack_on_success(self.imp_agent_app.pk, self.ilb_admin_user.pk)
            create_document_pack_on_success(self.exp_app.pk, self.ilb_admin_two_user.pk)
            create_document_pack_on_success(self.exp_agent_app.pk, self.ilb_admin_two_user.pk)

    def test_workbasket(self):
        self._test_ilb_admin_wb()
        self._test_importer_contact_wb()
        self._test_importer_agent_wb()
        self._test_exporter_contact_wb()
        self._test_exporter_agent_wb()

    def _test_ilb_admin_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Processing": {
                    "CHIEF Wait": [
                        "(TEST) Bypass CHIEF",
                        "(TEST) Bypass CHIEF induce failure",
                        "Monitor Progress",
                    ],
                    "Application Processing": ["View Case"],
                },
            },
            self.imp_agent_app.reference: {
                "Processing": {
                    "CHIEF Wait": [
                        "(TEST) Bypass CHIEF",
                        "(TEST) Bypass CHIEF induce failure",
                        "Monitor Progress",
                    ],
                    "Application Processing": ["View Case"],
                }
            },
        }
        check_expected_rows(self.ilb_admin_client, expected_rows)

        # Export apps are complete now so won't appear for caseworkers
        expected_rows = {}
        check_expected_rows(self.ilb_admin_two_client, expected_rows)

    def _test_importer_contact_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.importer_client, expected_rows)

        _remove_edit_permission(self.importer_user, self.imp_app.importer)
        expected_rows = {
            self.imp_app.reference: {"Processing": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.importer_client, expected_rows)

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.importer_agent_client, expected_rows)

        _remove_edit_permission(self.importer_agent_user, self.imp_agent_app.agent)
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.importer_agent_client, expected_rows)

    def _test_exporter_contact_wb(self):
        # Main org contacts see completed agent applications.
        expected_rows = {
            self.exp_app.reference: {
                "Completed": {
                    "Application View": ["View Application", "Clear"],
                    "Documents Issued 27-Jul-2023 10:06": ["View Issued Documents", "Clear"],
                }
            },
            self.exp_agent_app.reference: {
                "Completed": {"Application View": ["View Application", "Clear"]}
            },
        }

        check_expected_rows(self.exporter_client, expected_rows)

        _remove_edit_permission(self.exporter_user, self.exp_app.exporter)
        expected_rows = {
            self.exp_app.reference: {
                "Completed": {"Application View": ["View Application", "Clear"]}
            },
            self.exp_agent_app.reference: {
                "Completed": {"Application View": ["View Application", "Clear"]}
            },
        }
        check_expected_rows(self.exporter_client, expected_rows)

    def _test_exporter_agent_wb(self):
        expected_rows = {
            self.exp_agent_app.reference: {
                "Completed": {
                    "Application View": ["View Application", "Clear"],
                    "Documents Issued 27-Jul-2023 10:06": ["View Issued Documents", "Clear"],
                }
            }
        }

        check_expected_rows(self.exporter_agent_client, expected_rows)

        _remove_edit_permission(self.exporter_agent_user, self.exp_agent_app.agent)
        expected_rows = {
            self.exp_agent_app.reference: {
                "Completed": {"Application View": ["View Application", "Clear"]}
            }
        }
        check_expected_rows(self.exporter_agent_client, expected_rows)


class TestCompleteCaseWorkbasket(AuthTestCase):
    """Test workbasket rows where each case has been completed."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        _setup,
        fa_dfl_app_submitted,
        fa_dfl_agent_app_submitted,
        com_app_submitted,
        com_agent_app_submitted,
    ):
        self.imp_app = fa_dfl_app_submitted
        self.imp_agent_app = fa_dfl_agent_app_submitted
        self.exp_app = com_app_submitted
        self.exp_agent_app = com_agent_app_submitted

        _fix_access_request_data()

        # Take ownership of cases (two case officers)
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_app.pk, "import"))
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_agent_app.pk, "import"))
        self.ilb_admin_two_client.post(CaseURLS.take_ownership(self.exp_app.pk, "export"))
        self.ilb_admin_two_client.post(CaseURLS.take_ownership(self.exp_agent_app.pk, "export"))

        #
        # Complete checklists (import only)
        data = fa_dfl_checklist_form_data()
        self.ilb_admin_client.post(
            reverse("import:fa-dfl:manage-checklist", kwargs={"application_pk": self.imp_app.pk}),
            data=data,
        )
        self.ilb_admin_client.post(
            reverse(
                "import:fa-dfl:manage-checklist", kwargs={"application_pk": self.imp_agent_app.pk}
            ),
            data=data,
        )

        #
        # Complete response prep screen
        form_data = {"decision": ImportApplication.APPROVE}
        self.ilb_admin_client.post(
            CaseURLS.prepare_response(self.imp_app.pk, "import"), data=form_data
        )
        self.ilb_admin_client.post(
            CaseURLS.prepare_response(self.imp_agent_app.pk, "import"), data=form_data
        )
        self.ilb_admin_two_client.post(
            CaseURLS.prepare_response(self.exp_app.pk, "export"), data=form_data
        )
        self.ilb_admin_two_client.post(
            CaseURLS.prepare_response(self.exp_agent_app.pk, "export"), data=form_data
        )

        #
        # Set licence details (import only)
        start_date = dt.date.today()
        end_date = dt.date(start_date.year + 3, 1, 1)
        form_data = {
            "licence_start_date": start_date.strftime(JQUERY_DATE_FORMAT),
            "licence_end_date": end_date.strftime(JQUERY_DATE_FORMAT),
            "issue_paper_licence_only": False,
        }
        self.ilb_admin_client.post(
            reverse("import:edit-licence", kwargs={"application_pk": self.imp_app.pk}),
            data=form_data,
        )
        self.ilb_admin_client.post(
            reverse("import:edit-licence", kwargs={"application_pk": self.imp_agent_app.pk}),
            data=form_data,
        )

        #
        # Start authorisation
        self.ilb_admin_client.post(CaseURLS.start_authorisation(self.imp_app.pk, "import"))
        self.ilb_admin_client.post(CaseURLS.start_authorisation(self.imp_agent_app.pk, "import"))
        self.ilb_admin_two_client.post(CaseURLS.start_authorisation(self.exp_app.pk, "export"))
        self.ilb_admin_two_client.post(
            CaseURLS.start_authorisation(self.exp_agent_app.pk, "export")
        )

        #
        # Authorise Documents
        with patch("web.domains.case.views.views_misc.create_case_document_pack", autospec=True):
            form_data = {"password": "test"}
            self.ilb_admin_client.post(
                CaseURLS.authorise_documents(self.imp_app.pk, "import"), data=form_data
            )
            self.ilb_admin_client.post(
                CaseURLS.authorise_documents(self.imp_agent_app.pk, "import"), data=form_data
            )
            self.ilb_admin_two_client.post(
                CaseURLS.authorise_documents(self.exp_app.pk, "export"), data=form_data
            )
            self.ilb_admin_two_client.post(
                CaseURLS.authorise_documents(self.exp_agent_app.pk, "export"), data=form_data
            )

        with freezegun.freeze_time("2023-07-27 10:06:00"):
            # Manually call success task as we've faked creating the documents.
            create_document_pack_on_success(self.imp_app.pk, self.ilb_admin_user.pk)
            create_document_pack_on_success(self.imp_agent_app.pk, self.ilb_admin_user.pk)
            create_document_pack_on_success(self.exp_app.pk, self.ilb_admin_two_user.pk)
            create_document_pack_on_success(self.exp_agent_app.pk, self.ilb_admin_two_user.pk)

            #
            # Bypass chief for import applications
            with patch(
                "web.domains.chief.utils.send_completed_application_process_notifications",
                autospec=True,
            ):
                self.ilb_admin_client.post(
                    reverse(
                        "import:bypass-chief",
                        kwargs={"application_pk": self.imp_app.pk, "chief_status": "success"},
                    )
                )

                self.ilb_admin_client.post(
                    reverse(
                        "import:bypass-chief",
                        kwargs={"application_pk": self.imp_agent_app.pk, "chief_status": "success"},
                    )
                )

    def test_workbasket(self):
        self._test_ilb_admin_wb()
        self._test_importer_contact_wb()
        self._test_importer_agent_wb()
        self._test_exporter_contact_wb()
        self._test_exporter_agent_wb()

    def _test_ilb_admin_wb(self):
        expected_rows = {}
        check_expected_rows(self.ilb_admin_client, expected_rows)

        expected_rows = {}
        check_expected_rows(self.ilb_admin_two_client, expected_rows)

    def _test_importer_contact_wb(self):
        # Main org contacts see completed agent applications.
        expected_rows = {
            self.imp_app.reference: {
                "Completed": {
                    "Application View": ["View Application", "Clear"],
                    "Documents Issued 27-Jul-2023 10:06": ["View Issued Documents", "Clear"],
                    "Firearms Supplementary Reporting": ["Provide Report"],
                }
            },
            self.imp_agent_app.reference: {
                "Completed": {"Application View": ["View Application", "Clear"]}
            },
        }

        check_expected_rows(self.importer_client, expected_rows)

        _remove_edit_permission(self.importer_user, self.imp_app.importer)
        expected_rows = {
            self.imp_app.reference: {
                "Completed": {"Application View": ["View Application", "Clear"]}
            },
            self.imp_agent_app.reference: {
                "Completed": {"Application View": ["View Application", "Clear"]}
            },
        }
        check_expected_rows(self.importer_client, expected_rows)

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Completed": {
                    "Application View": ["View Application", "Clear"],
                    "Documents Issued 27-Jul-2023 10:06": ["View Issued Documents", "Clear"],
                    "Firearms Supplementary Reporting": ["Provide Report"],
                }
            }
        }

        check_expected_rows(self.importer_agent_client, expected_rows)

        _remove_edit_permission(self.importer_agent_user, self.imp_agent_app.agent)
        expected_rows = {
            self.imp_agent_app.reference: {
                "Completed": {"Application View": ["View Application", "Clear"]}
            }
        }
        check_expected_rows(self.importer_agent_client, expected_rows)

    def _test_exporter_contact_wb(self):
        # Main org contacts see completed agent applications.
        expected_rows = {
            self.exp_app.reference: {
                "Completed": {
                    "Application View": ["View Application", "Clear"],
                    "Documents Issued 27-Jul-2023 10:06": ["View Issued Documents", "Clear"],
                }
            },
            self.exp_agent_app.reference: {
                "Completed": {"Application View": ["View Application", "Clear"]}
            },
        }

        check_expected_rows(self.exporter_client, expected_rows)

        _remove_edit_permission(self.exporter_user, self.exp_app.exporter)
        expected_rows = {
            self.exp_app.reference: {
                "Completed": {"Application View": ["View Application", "Clear"]}
            },
            self.exp_agent_app.reference: {
                "Completed": {"Application View": ["View Application", "Clear"]}
            },
        }
        check_expected_rows(self.exporter_client, expected_rows)

    def _test_exporter_agent_wb(self):
        expected_rows = {
            self.exp_agent_app.reference: {
                "Completed": {
                    "Application View": ["View Application", "Clear"],
                    "Documents Issued 27-Jul-2023 10:06": ["View Issued Documents", "Clear"],
                }
            }
        }

        check_expected_rows(self.exporter_agent_client, expected_rows)

        _remove_edit_permission(self.exporter_agent_user, self.exp_agent_app.agent)
        expected_rows = {
            self.exp_agent_app.reference: {
                "Completed": {"Application View": ["View Application", "Clear"]}
            }
        }
        check_expected_rows(self.exporter_agent_client, expected_rows)


class TestCompleteCaseCHIEFFailWorkbasket(AuthTestCase):
    """Test workbasket rows where each case has been completed."""

    @pytest.fixture(autouse=True)
    def setup(self, _setup, fa_dfl_app_submitted, fa_dfl_agent_app_submitted):
        self.imp_app = fa_dfl_app_submitted
        self.imp_agent_app = fa_dfl_agent_app_submitted

        _fix_access_request_data()

        # Take ownership of cases (two case officers)
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_app.pk, "import"))
        self.ilb_admin_client.post(CaseURLS.take_ownership(self.imp_agent_app.pk, "import"))

        #
        # Complete checklists (import only)
        data = fa_dfl_checklist_form_data()
        self.ilb_admin_client.post(
            reverse("import:fa-dfl:manage-checklist", kwargs={"application_pk": self.imp_app.pk}),
            data=data,
        )
        self.ilb_admin_client.post(
            reverse(
                "import:fa-dfl:manage-checklist", kwargs={"application_pk": self.imp_agent_app.pk}
            ),
            data=data,
        )

        #
        # Complete response prep screen
        form_data = {"decision": ImportApplication.APPROVE}
        self.ilb_admin_client.post(
            CaseURLS.prepare_response(self.imp_app.pk, "import"), data=form_data
        )
        self.ilb_admin_client.post(
            CaseURLS.prepare_response(self.imp_agent_app.pk, "import"), data=form_data
        )

        #
        # Set licence details (import only)
        start_date = dt.date.today()
        end_date = dt.date(start_date.year + 3, 1, 1)
        form_data = {
            "licence_start_date": start_date.strftime(JQUERY_DATE_FORMAT),
            "licence_end_date": end_date.strftime(JQUERY_DATE_FORMAT),
            "issue_paper_licence_only": False,
        }
        self.ilb_admin_client.post(
            reverse("import:edit-licence", kwargs={"application_pk": self.imp_app.pk}),
            data=form_data,
        )
        self.ilb_admin_client.post(
            reverse("import:edit-licence", kwargs={"application_pk": self.imp_agent_app.pk}),
            data=form_data,
        )

        #
        # Start authorisation
        self.ilb_admin_client.post(CaseURLS.start_authorisation(self.imp_app.pk, "import"))
        self.ilb_admin_client.post(CaseURLS.start_authorisation(self.imp_agent_app.pk, "import"))

        #
        # Authorise Documents
        with patch("web.domains.case.views.views_misc.create_case_document_pack", autospec=True):
            form_data = {"password": "test"}
            self.ilb_admin_client.post(
                CaseURLS.authorise_documents(self.imp_app.pk, "import"), data=form_data
            )
            self.ilb_admin_client.post(
                CaseURLS.authorise_documents(self.imp_agent_app.pk, "import"), data=form_data
            )

        with freezegun.freeze_time("2023-07-27 10:06:00"):
            # Manually call success task as we've faked creating the documents.
            create_document_pack_on_success(self.imp_app.pk, self.ilb_admin_user.pk)
            create_document_pack_on_success(self.imp_agent_app.pk, self.ilb_admin_user.pk)

            #
            # Bypass chief for import applications
            with patch(
                "web.domains.chief.utils.send_completed_application_process_notifications",
                autospec=True,
            ):
                self.ilb_admin_client.post(
                    reverse(
                        "import:bypass-chief",
                        kwargs={"application_pk": self.imp_app.pk, "chief_status": "failure"},
                    )
                )

                self.ilb_admin_client.post(
                    reverse(
                        "import:bypass-chief",
                        kwargs={"application_pk": self.imp_agent_app.pk, "chief_status": "failure"},
                    )
                )

    def test_workbasket(self):
        self._test_ilb_admin_wb()
        self._test_importer_contact_wb()
        self._test_importer_agent_wb()

    def _test_ilb_admin_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Processing": {
                    "CHIEF Error": ["Show Licence Details"],
                    "Application Processing": ["View"],
                }
            },
            self.imp_agent_app.reference: {
                "Processing": {
                    "CHIEF Error": ["Show Licence Details"],
                    "Application Processing": ["View"],
                }
            },
        }
        check_expected_rows(self.ilb_admin_client, expected_rows)

    def _test_importer_contact_wb(self):
        expected_rows = {
            self.imp_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.importer_client, expected_rows)

        _remove_edit_permission(self.importer_user, self.imp_app.importer)
        expected_rows = {
            self.imp_app.reference: {"Processing": {"Application Submitted": ["View Application"]}}
        }
        check_expected_rows(self.importer_client, expected_rows)

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.importer_agent_client, expected_rows)

        _remove_edit_permission(self.importer_agent_user, self.imp_agent_app.agent)
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["View Application"]}
            }
        }
        check_expected_rows(self.importer_agent_client, expected_rows)


class TestMailshotsAppearInWorkbasket(AuthTestCase):
    """Test workbasket rows with mailshots."""

    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.all_org_mailshot = self._create_mailshot(
            "All Org Mailshot", "MAIL/1", is_to_importers=True, is_to_exporters=True
        )
        self.exporter_mailshot = self._create_mailshot(
            "Exporter Mailshot", "MAIL/2", is_to_exporters=True
        )
        self.importer_mailshot = self._create_mailshot(
            "Importer Mailshot", "MAIL/3", is_to_importers=True
        )
        self.draft_all_org_mailshot = self._create_mailshot(
            "All Org Mailshot",
            "MAIL/4",
            status=Mailshot.Statuses.DRAFT,
            is_to_importers=True,
            is_to_exporters=True,
        )

        _fix_access_request_data()

    def test_workbasket(self):
        self._test_ilb_admin_wb()
        self._test_importer_contact_wb()
        self._test_importer_agent_wb()
        self._test_exporter_contact_wb()
        self._test_exporter_agent_wb()

    def _test_ilb_admin_wb(self):
        expected_rows = {}
        check_expected_rows(self.ilb_admin_client, expected_rows)

    def _test_importer_contact_wb(self):
        expected_rows = {
            self.all_org_mailshot.get_reference(): {
                "Published": {"Mailshot Received": ["View", "Clear"]}
            },
            self.importer_mailshot.get_reference(): {
                "Published": {"Mailshot Received": ["View", "Clear"]}
            },
        }

        check_expected_rows(self.importer_client, expected_rows)

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.all_org_mailshot.get_reference(): {
                "Published": {"Mailshot Received": ["View", "Clear"]}
            },
            self.importer_mailshot.get_reference(): {
                "Published": {"Mailshot Received": ["View", "Clear"]}
            },
        }

        check_expected_rows(self.importer_agent_client, expected_rows)

    def _test_exporter_contact_wb(self):
        expected_rows = {
            self.all_org_mailshot.get_reference(): {
                "Published": {"Mailshot Received": ["View", "Clear"]}
            },
            self.exporter_mailshot.get_reference(): {
                "Published": {"Mailshot Received": ["View", "Clear"]}
            },
        }

        check_expected_rows(self.exporter_client, expected_rows)

    def _test_exporter_agent_wb(self):
        expected_rows = {
            self.all_org_mailshot.get_reference(): {
                "Published": {"Mailshot Received": ["View", "Clear"]}
            },
            self.exporter_mailshot.get_reference(): {
                "Published": {"Mailshot Received": ["View", "Clear"]}
            },
        }
        check_expected_rows(self.exporter_agent_client, expected_rows)

    def _create_mailshot(
        self,
        title,
        reference,
        version=1,
        *,
        description="Test Desc",
        status=Mailshot.Statuses.PUBLISHED,
        is_to_exporters=False,
        is_to_importers=False,
    ):
        template = Template.objects.get(template_code="PUBLISH_MAILSHOT")
        mailshot = Mailshot(
            title=title,
            description=description,
            status=status,
            is_email=True,
            email_subject=template.template_title,
            email_body=template.template_content,
            created_by=self.ilb_admin_user,
            is_to_exporters=is_to_exporters,
            is_to_importers=is_to_importers,
            reference=reference,
            version=version,
        )

        if status == Mailshot.Statuses.PUBLISHED:
            mailshot.published_datetime = timezone.now()
            mailshot.order_datetime = mailshot.published_datetime
            mailshot.process_type = "MAILSHOT"

        mailshot.save()

        return mailshot


class TestAccessRequestsWorkbasket(AuthTestCase):
    ar_user: User
    ar_user_client: Client
    iar: ImporterAccessRequest
    ear: ExporterAccessRequest

    @pytest.fixture(autouse=True)
    def setup(
        self,
        _setup,
        importer_access_request,
        exporter_access_request,
        access_request_user_client,
        access_request_user,
    ):
        self.ar_user_client = access_request_user_client
        self.ar_user = access_request_user
        self.iar = get_linked_access_request(importer_access_request, self.importer)
        self.ear = get_linked_access_request(exporter_access_request, self.exporter)

    def test_access_request_submitted(self):
        ar_user_expected_rows = {
            "ear/1": {"Submitted": {"Access Request": ["View"]}},
            "iar/1": {"Submitted": {"Access Request": ["View"]}},
        }
        check_expected_rows(self.ar_user_client, ar_user_expected_rows)

        ilb_expected_rows = {
            "ear/1": {"Submitted": {"Access Request": ["Manage"]}},
            "iar/1": {"Submitted": {"Access Request": ["Manage"]}},
        }
        check_expected_rows(self.ilb_admin_client, ilb_expected_rows)

    def test_access_request_submitted_further_information_requested(self):
        self._add_fir(self.iar, FurtherInformationRequest.OPEN)
        self._add_fir(self.ear, FurtherInformationRequest.OPEN)

        ar_user_expected_rows = {
            "ear/1": {
                "Submitted": {
                    "Access Request\nFurther Information Requested": ["View", "Respond FIR"]
                }
            },
            "iar/1": {
                "Submitted": {
                    "Access Request\nFurther Information Requested": ["View", "Respond FIR"]
                }
            },
        }
        check_expected_rows(self.ar_user_client, ar_user_expected_rows)

        ilb_expected_rows = {
            "ear/1": {"Submitted": {"Access Request\nFurther Information Requested": ["Manage"]}},
            "iar/1": {"Submitted": {"Access Request\nFurther Information Requested": ["Manage"]}},
        }
        check_expected_rows(self.ilb_admin_client, ilb_expected_rows)

    def test_access_request_submitted_further_information_responded(self):
        self._add_fir(
            self.iar,
            FurtherInformationRequest.RESPONDED,
            response_datetime=timezone.now(),
            response_by=self.ar_user,
        )
        self._add_fir(
            self.ear,
            FurtherInformationRequest.RESPONDED,
            response_datetime=timezone.now(),
            response_by=self.ar_user,
        )

        ar_user_expected_rows = {
            "ear/1": {"Submitted": {"Access Request": ["View"]}},
            "iar/1": {"Submitted": {"Access Request": ["View"]}},
        }
        check_expected_rows(self.ar_user_client, ar_user_expected_rows)

        ilb_expected_rows = {
            "ear/1": {"Submitted": {"Access Request": ["Manage"]}},
            "iar/1": {"Submitted": {"Access Request": ["Manage"]}},
        }
        check_expected_rows(self.ilb_admin_client, ilb_expected_rows)

    def test_access_request_approval_requested_not_assigned(self):
        add_approval_request(self.iar, self.ilb_admin_user)
        add_approval_request(self.ear, self.ilb_admin_user)

        ar_user_expected_rows = {
            "ear/1": {"Submitted": {"Access Request": ["View"]}},
            "iar/1": {"Submitted": {"Access Request": ["View"]}},
        }
        check_expected_rows(self.ar_user_client, ar_user_expected_rows)

        ilb_expected_rows = {
            "ear/1": {"Submitted": {"Access Request\nApproval Requested": ["Manage"]}},
            "iar/1": {"Submitted": {"Access Request\nApproval Requested": ["Manage"]}},
        }
        check_expected_rows(self.ilb_admin_client, ilb_expected_rows)

        importer_user_expected_rows = {"iar/1": {"OPEN": {"Approval Request": ["Take Ownership"]}}}
        check_expected_rows(self.importer_client, importer_user_expected_rows)

        exporter_user_expected_rows = {
            "ear/1": {"OPEN": {"Approval Request": ["Take Ownership"]}},
        }
        check_expected_rows(self.exporter_client, exporter_user_expected_rows)

    def test_access_request_approval_requested_by_user(self):
        add_approval_request(self.iar, self.ilb_admin_user, self.importer_user)
        add_approval_request(self.ear, self.ilb_admin_user, self.exporter_user)

        ar_user_expected_rows = {
            "ear/1": {"Submitted": {"Access Request": ["View"]}},
            "iar/1": {"Submitted": {"Access Request": ["View"]}},
        }
        check_expected_rows(self.ar_user_client, ar_user_expected_rows)

        ilb_expected_rows = {
            "ear/1": {"Submitted": {"Access Request\nApproval Requested": ["Manage"]}},
            "iar/1": {"Submitted": {"Access Request\nApproval Requested": ["Manage"]}},
        }
        check_expected_rows(self.ilb_admin_client, ilb_expected_rows)

        importer_user_expected_rows = {"iar/1": {"OPEN": {"Approval Request": ["Manage"]}}}
        check_expected_rows(self.importer_client, importer_user_expected_rows)

        exporter_user_expected_rows = {
            "ear/1": {"OPEN": {"Approval Request": ["Manage"]}},
        }
        check_expected_rows(self.exporter_client, exporter_user_expected_rows)

    def test_access_request_approval_confirmed(self):
        add_approval_request(
            self.iar, self.ilb_admin_user, self.importer_user, ApprovalRequest.Statuses.COMPLETED
        )
        self.iar.response = ApprovalRequest.Responses.APPROVE
        self.iar.response_by = self.importer_user
        self.iar.response_date = timezone.now()
        self.iar.save()

        add_approval_request(
            self.ear, self.ilb_admin_user, self.exporter_user, ApprovalRequest.Statuses.COMPLETED
        )
        self.ear.response = ApprovalRequest.Responses.APPROVE
        self.ear.response_by = self.importer_user
        self.ear.response_date = timezone.now()
        self.ear.save()

        ar_user_expected_rows = {
            "ear/1": {"Submitted": {"Access Request": ["View"]}},
            "iar/1": {"Submitted": {"Access Request": ["View"]}},
        }
        check_expected_rows(self.ar_user_client, ar_user_expected_rows)

        ilb_expected_rows = {
            "ear/1": {"Submitted": {"Access Request\nApproval Complete": ["Manage"]}},
            "iar/1": {"Submitted": {"Access Request\nApproval Complete": ["Manage"]}},
        }
        check_expected_rows(self.ilb_admin_client, ilb_expected_rows)

        importer_user_expected_rows = {}
        check_expected_rows(self.importer_client, importer_user_expected_rows)

        exporter_user_expected_rows = {}
        check_expected_rows(self.exporter_client, exporter_user_expected_rows)

    def test_access_request_approval_rejected(self):
        add_approval_request(
            self.iar, self.ilb_admin_user, self.importer_user, ApprovalRequest.Statuses.COMPLETED
        )
        self.iar.response = ApprovalRequest.Responses.APPROVE
        self.iar.response_by = self.importer_user
        self.iar.response_date = timezone.now()
        self.iar.response_reason = "test reason"
        self.iar.save()

        add_approval_request(
            self.ear, self.ilb_admin_user, self.exporter_user, ApprovalRequest.Statuses.COMPLETED
        )
        self.ear.response = ApprovalRequest.Responses.APPROVE
        self.ear.response_by = self.importer_user
        self.ear.response_date = timezone.now()
        self.ear.response_reason = "test reason"
        self.ear.save()

        ar_user_expected_rows = {
            "ear/1": {"Submitted": {"Access Request": ["View"]}},
            "iar/1": {"Submitted": {"Access Request": ["View"]}},
        }
        check_expected_rows(self.ar_user_client, ar_user_expected_rows)

        ilb_expected_rows = {
            "ear/1": {"Submitted": {"Access Request\nApproval Complete": ["Manage"]}},
            "iar/1": {"Submitted": {"Access Request\nApproval Complete": ["Manage"]}},
        }
        check_expected_rows(self.ilb_admin_client, ilb_expected_rows)

        importer_user_expected_rows = {}
        check_expected_rows(self.importer_client, importer_user_expected_rows)

        exporter_user_expected_rows = {}
        check_expected_rows(self.exporter_client, exporter_user_expected_rows)

    def test_access_request_complete_approved(self):
        self.iar.status = AccessRequest.Statuses.CLOSED
        self.iar.response = AccessRequest.APPROVED
        self.iar.save()

        self.ear.status = AccessRequest.Statuses.CLOSED
        self.ear.response = AccessRequest.APPROVED
        self.ear.save()

        ar_user_expected_rows = {}
        check_expected_rows(self.ar_user_client, ar_user_expected_rows)

        ilb_expected_rows = {}
        check_expected_rows(self.ilb_admin_client, ilb_expected_rows)

    def test_access_request_complete_rejected(self):
        self.iar.status = AccessRequest.Statuses.CLOSED
        self.iar.response = AccessRequest.REFUSED
        self.iar.response_reason = "test reason"
        self.iar.save()

        self.ear.status = AccessRequest.Statuses.CLOSED
        self.ear.response = AccessRequest.REFUSED
        self.ear.response_reason = "test reason"
        self.ear.save()

        ar_user_expected_rows = {}
        check_expected_rows(self.ar_user_client, ar_user_expected_rows)

        ilb_expected_rows = {}
        check_expected_rows(self.ilb_admin_client, ilb_expected_rows)

    def _add_fir(self, ar: AccessRequest, status: str, **kwargs) -> None:
        ar.further_information_requests.create(
            status=status,
            requested_by=self.ilb_admin_user,
            request_subject="Test subject",
            request_detail="Test detail",
            process_type=FurtherInformationRequest.PROCESS_TYPE,
            **kwargs,
        )


def check_expected_rows(
    client: Client, expected_rows: dict[str, dict[str, dict[str, list[str]]]]
) -> None:
    url = reverse("workbasket")
    response = client.get(url)

    rows: list[WorkbasketRow] = response.context["rows"]

    # Check the references match
    assert sorted([r.reference for r in rows]) == sorted(expected_rows.keys())

    # iterate over rows and check the data in expected_rows
    for row in rows:
        expected_row = expected_rows[row.reference]

        for status, sections in expected_row.items():
            assert row.status == status

            # Check the section labels match
            assert sorted([s.information for s in row.sections]) == sorted(sections.keys())

            # For each section check the action names match
            for section in row.sections:
                expected_actions = sections[section.information]

                assert sorted([a.name for a in section.actions]) == sorted(expected_actions)


def fa_dfl_checklist_form_data() -> dict[str, Any]:
    return {
        # Base fields
        "case_update": YesNoNAChoices.yes,
        "fir_required": YesNoNAChoices.no,
        "response_preparation": True,
        "validity_period_correct": YesNoNAChoices.yes,
        "endorsements_listed": YesNoNAChoices.yes,
        "authorisation": YesNoNAChoices.yes,
        # app specific fields
        "deactivation_certificate_attached": YesNoNAChoices.yes,
        "deactivation_certificate_issued": YesNoNAChoices.yes,
    }


def _fix_access_request_data():
    """There are other tests that require one of several access requests to exist.

    These fixtures cause the access requests to appear in the caseworker workbaskets:
        - access_request_user
        - importer_access_request
        - exporter_access_request
    """
    AccessRequest.objects.all().delete()


def _remove_edit_permission(user: User, org: Importer | Exporter) -> None:
    match org:
        case Importer():
            perm = Perms.obj.importer.edit
        case Exporter():
            perm = Perms.obj.exporter.edit
        case _:
            raise ValueError(f"Unknown Org: {org}")

    remove_perm(perm, user, org)
