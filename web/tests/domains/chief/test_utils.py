import datetime

import pytest

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
    def _setup(self, fa_sil_app_with_chief, test_import_user):
        self.app = fa_sil_app_with_chief
        self.user = test_import_user

        # Current draft licence
        self.licence = self.app.licences.get(status=ImportApplicationLicence.Status.DRAFT)

        # Current active task
        self.chief_wait_task = self.app.tasks.get(task_type=Task.TaskType.CHIEF_WAIT)

        # The current LiteHMRCChiefRequest record
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
            status=VariationRequest.OPEN,
            what_varied="Dummy what_varied",
            why_varied="Dummy why_varied",
            when_varied=datetime.date.today(),
            requested_by=self.user,
        )

        utils.chief_licence_reply_approve_licence(self.app)

        check_licence_approve_correct(self.app, self.licence, self.chief_wait_task)

        # Check variation has been updated
        variation.refresh_from_db()

        assert variation.status == VariationRequest.ACCEPTED

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
