import datetime
from typing import Any
from unittest.mock import patch

import freezegun
import pytest
from django.test.client import Client
from django.urls import reverse

from web.domains.case.tasks import create_document_pack_on_success
from web.domains.workbasket.base import WorkbasketRow
from web.forms.fields import JQUERY_DATE_FORMAT
from web.models import AccessRequest, ImportApplication
from web.models.shared import YesNoNAChoices
from web.tests.auth.auth import AuthTestCase
from web.tests.helpers import CaseURLS


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

    def _test_importer_agent_wb(self):
        expected_rows = {
            # self.imp_agent_app.reference == "Not Assigned"
            "Not Assigned": {"In Progress": {"Prepare Application": ["Resume", "Cancel"]}}
        }

        check_expected_rows(self.importer_agent_client, expected_rows)

    def _test_exporter_contact_wb(self):
        expected_rows = {
            # self.exp_app.reference == "Not Assigned"
            "Not Assigned": {"In Progress": {"Prepare Application": ["Resume", "Cancel"]}}
        }

        check_expected_rows(self.exporter_client, expected_rows)

    def _test_exporter_agent_wb(self):
        expected_rows = {
            # self.exp_agent_app.reference == "Not Assigned"
            "Not Assigned": {"In Progress": {"Prepare Application": ["Resume", "Cancel"]}}
        }

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

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Submitted": {"Application Submitted": ["Request Withdrawal", "View Application"]}
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

    def _test_exporter_agent_wb(self):
        expected_rows = {
            self.exp_agent_app.reference: {
                "Submitted": {"Application Submitted": ["Request Withdrawal", "View Application"]}
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

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
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

    def _test_exporter_agent_wb(self):
        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
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

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Submitted": {"Application Submitted": ["Pending Withdrawal", "View Application"]}
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

    def _test_exporter_agent_wb(self):
        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Pending Withdrawal", "View Application"]}
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
        start_date = datetime.date.today()
        end_date = datetime.date(start_date.year + 3, 1, 1)
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

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
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

    def _test_exporter_agent_wb(self):
        expected_rows = {
            self.exp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
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
        start_date = datetime.date.today()
        end_date = datetime.date(start_date.year + 3, 1, 1)
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

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
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
                "Completed": {
                    "Application View": ["View Application", "Clear"],
                }
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
        start_date = datetime.date.today()
        end_date = datetime.date(start_date.year + 3, 1, 1)
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
                "Completed": {
                    "Application View": ["View Application", "Clear"],
                }
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
                "Completed": {
                    "Application View": ["View Application", "Clear"],
                }
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
        start_date = datetime.date.today()
        end_date = datetime.date(start_date.year + 3, 1, 1)
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

    def _test_importer_agent_wb(self):
        expected_rows = {
            self.imp_agent_app.reference: {
                "Processing": {"Application Submitted": ["Request Withdrawal", "View Application"]}
            }
        }

        check_expected_rows(self.importer_agent_client, expected_rows)


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
