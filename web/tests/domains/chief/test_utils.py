import datetime as dt

import pytest

from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.domains.chief import types, utils
from web.models import ImportApplicationLicence, Task, VariationRequest

from .conftest import (
    check_complete_chief_request_correct,
    check_fail_chief_request_correct,
    check_licence_approve_correct,
    check_licence_reject_correct,
)


class TestChiefUtils:
    @pytest.fixture(autouse=True)
    def _setup(self, fa_sil_app_with_chief, importer_one_contact):
        self.app = fa_sil_app_with_chief
        self.user = importer_one_contact

        # Current draft licence
        self.licence = self.app.licences.get(status=ImportApplicationLicence.Status.DRAFT)

        # Current active task
        self.chief_wait_task = self.app.tasks.get(task_type=Task.TaskType.CHIEF_WAIT)

        # The current ICMSHMRCChiefRequest record
        self.chief_req = self.app.chief_references.first()

    def test_chief_licence_reply_approve_licence(self):
        utils.chief_licence_reply_approve_licence(self.app)

        check_licence_approve_correct(self.app, self.licence, self.chief_wait_task)

    def test_chief_licence_reply_approve_when_app_has_a_variation_request(self):
        # Fake a variation request
        self.app.status = ImpExpStatus.VARIATION_REQUESTED
        self.app.reference = f"{self.app.reference}/1"
        self.app.save()

        variation = self.app.variation_requests.create(
            status=VariationRequest.Statuses.OPEN,
            what_varied="Dummy what_varied",
            why_varied="Dummy why_varied",
            when_varied=dt.date.today(),
            requested_by=self.user,
        )

        utils.chief_licence_reply_approve_licence(self.app)

        check_licence_approve_correct(self.app, self.licence, self.chief_wait_task)

        # Check variation has been updated
        variation.refresh_from_db()

        assert variation.status == VariationRequest.Statuses.ACCEPTED

    def test_chief_licence_reply_reject_licence(self):
        utils.chief_licence_reply_reject_licence(self.app)

        check_licence_reject_correct(self.app, self.licence, self.chief_wait_task)

    def test_complete_chief_request(self):
        utils.complete_chief_request(self.chief_req)

        check_complete_chief_request_correct(self.chief_req)

    def test_fail_chief_request(self):
        errors = [types.ResponseError(error_code=1, error_msg="Test error message")]
        utils.fail_chief_request(self.chief_req, errors)

        check_fail_chief_request_correct(self.chief_req)

    def test_chief_licence_reply_approve_licence_revoked_app(self):
        # Setup - fake revoking a licence
        self.app.status = ImpExpStatus.REVOKED
        self.app.save()
        self.app.tasks.update(is_active=False)
        Task.objects.create(process=self.app, task_type=Task.TaskType.CHIEF_REVOKE_WAIT)

        # Test
        utils.chief_licence_reply_approve_licence(self.app)

        # Asserts
        case_progress.check_expected_status(self.app, [ImpExpStatus.REVOKED])
        assert Task.TaskType.CHIEF_REVOKE_WAIT not in case_progress.get_active_task_list(self.app)

    def test_chief_licence_reply_reject_licence_revoked_app(self):
        # Setup - fake revoking a licence
        self.app.status = ImpExpStatus.REVOKED
        self.app.save()
        self.app.tasks.update(is_active=False)
        Task.objects.create(process=self.app, task_type=Task.TaskType.CHIEF_REVOKE_WAIT)

        # Test
        utils.chief_licence_reply_reject_licence(self.app)

        # Asserts
        case_progress.check_expected_status(self.app, [ImpExpStatus.REVOKED])
        assert Task.TaskType.CHIEF_REVOKE_WAIT not in case_progress.get_active_task_list(self.app)
        case_progress.check_expected_task(self.app, Task.TaskType.CHIEF_ERROR)
