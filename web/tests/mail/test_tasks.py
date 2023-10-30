import datetime
from unittest import mock

import freezegun
import pytest
from celery.result import EagerResult
from django.utils import timezone

from web.mail.tasks import (
    get_expiring_importers_details,
    send_authority_expiring_firearms_email_task,
    send_authority_expiring_section_5_email_task,
    send_mailshot_email_task,
    send_retract_mailshot_email_task,
)
from web.mail.types import ImporterDetails
from web.models import Constabulary, FirearmsAuthority, Section5Authority
from web.tests.auth import AuthTestCase


class TestMailTasks(AuthTestCase):
    @pytest.fixture
    def section_5_authorities(self):
        Section5Authority.objects.create(
            importer=self.importer,
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True,
            reference="11/A/D/0001",
        )
        Section5Authority.objects.create(
            importer=self.importer,
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True,
            reference="12/A/D/0001",
        )
        Section5Authority.objects.create(
            importer=self.importer_two,
            start_date=self.start_date,
            end_date=self.end_date + datetime.timedelta(days=1),
            is_active=True,
            reference="13/A/D/0001",
        )
        Section5Authority.objects.create(
            importer=self.importer,
            start_date=self.start_date,
            end_date=self.end_date - datetime.timedelta(days=1),
            is_active=True,
            reference="14/A/D/0001",
        )
        Section5Authority.objects.create(
            importer=self.importer,
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=False,
            reference="15/A/D/0001",
        )
        Section5Authority.objects.create(
            importer=self.importer_two,
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True,
            reference="16/A/D/0001",
        )

    @pytest.fixture
    def firearms_authorities(self):
        FirearmsAuthority.objects.create(
            importer=self.importer,
            issuing_constabulary=self.derbyshire,
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True,
            reference="11/A/D/0001",
        )
        FirearmsAuthority.objects.create(
            importer=self.importer,
            issuing_constabulary=self.cheshire,
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True,
            reference="12/A/D/0001",
        )
        FirearmsAuthority.objects.create(
            importer=self.importer_two,
            issuing_constabulary=self.derbyshire,
            start_date=self.start_date,
            end_date=self.end_date + datetime.timedelta(days=1),
            is_active=True,
            reference="13/A/D/0001",
        )
        FirearmsAuthority.objects.create(
            importer=self.importer,
            issuing_constabulary=self.derbyshire,
            start_date=self.start_date,
            end_date=self.end_date - datetime.timedelta(days=1),
            is_active=True,
            reference="14/A/D/0001",
        )
        FirearmsAuthority.objects.create(
            importer=self.importer,
            issuing_constabulary=self.cheshire,
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=False,
            reference="15/A/D/0001",
        )
        FirearmsAuthority.objects.create(
            importer=self.importer_two,
            issuing_constabulary=self.derbyshire,
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True,
            reference="16/A/D/0001",
        )

    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.derbyshire = Constabulary.objects.get(name="Derbyshire")
        self.cheshire = Constabulary.objects.get(name="Cheshire")
        self.start_date = datetime.date(2020, 2, 16) - datetime.timedelta(days=10)
        self.end_date = datetime.date(2020, 2, 16) + datetime.timedelta(days=30)

    @mock.patch("web.mail.tasks.send_retract_mailshot_email")
    def test_send_retract_mailshot_email_task(self, mock_send_email, draft_mailshot):
        mock_send_email.return_value = None
        celery_result: EagerResult = send_retract_mailshot_email_task.delay(draft_mailshot.pk)
        assert celery_result.successful() is True
        assert mock_send_email.called is True

    @mock.patch("web.mail.tasks.send_mailshot_email")
    def test_send_mailshot_email_task(self, mock_send_email, draft_mailshot):
        celery_result: EagerResult = send_mailshot_email_task.delay(draft_mailshot.pk)
        assert celery_result.successful() is True
        assert mock_send_email.called is True

    def test_get_expiring_importers_details_for_section_5_authority(self, section_5_authorities):
        assert get_expiring_importers_details(Section5Authority, self.end_date, None) == [
            {
                "authority_refs": "11/A/D/0001, 12/A/D/0001",
                "id": 1,
                "name": "Test Importer 1",
            },
            {"authority_refs": "16/A/D/0001", "id": 3, "name": "Test Importer 2"},
        ]

    def test_get_expiring_importers_details_for_firearms_authority(self, firearms_authorities):
        assert get_expiring_importers_details(
            FirearmsAuthority, self.end_date, self.derbyshire
        ) == [
            {
                "authority_refs": "11/A/D/0001",
                "id": 1,
                "name": "Test Importer 1",
            },
            {"authority_refs": "16/A/D/0001", "id": 3, "name": "Test Importer 2"},
        ]

    @freezegun.freeze_time("2020-02-16 12:00:00")
    @mock.patch("web.mail.tasks.send_authority_expiring_section_5_email")
    @mock.patch("web.mail.tasks.get_expiring_importers_details")
    def test_send_authority_expiring_section_5_email_task_when_no_importers_found(
        self, mock_get_importer_details, mock_send_email
    ):
        mock_get_importer_details.return_value = []
        send_authority_expiring_section_5_email_task.delay()
        assert mock_get_importer_details.called is True
        assert mock_send_email.called is False
        mock_get_importer_details.assert_any_call(
            Section5Authority, datetime.date(2020, 3, 17), None
        )

    @freezegun.freeze_time("2020-02-16 12:00:00")
    @mock.patch("web.mail.tasks.send_authority_expiring_section_5_email")
    @mock.patch("web.mail.tasks.get_expiring_importers_details")
    def test_send_authority_expiring_section_5_email_task(
        self, mock_get_importer_details, mock_send_email
    ):
        importers = [ImporterDetails(id=1, name="Importer 1", authority_refs="12345,67890")]

        mock_get_importer_details.return_value = importers
        send_authority_expiring_section_5_email_task.delay()
        assert mock_get_importer_details.called is True
        assert mock_send_email.called is True
        mock_send_email.assert_any_call(importers, datetime.date(2020, 3, 17))

    @mock.patch("web.mail.tasks.send_authority_expiring_firearms_email")
    @mock.patch("web.mail.tasks.get_expiring_importers_details")
    def test_send_authority_expiring_firearms_email_task_when_no_constabularies(
        self, mock_get_importer_details, mock_send_email
    ):
        mock_get_importer_details.return_value = []
        send_authority_expiring_firearms_email_task.delay()
        assert mock_get_importer_details.called is False
        assert mock_send_email.called is False

    @mock.patch("web.mail.tasks.send_authority_expiring_firearms_email")
    @mock.patch("web.mail.tasks.get_expiring_importers_details")
    def test_send_authority_expiring_firearms_email_task_no_importers(
        self, mock_get_importer_details, mock_send_email
    ):
        start_date = timezone.now().date() - datetime.timedelta(days=10)
        end_date = timezone.now().date() + datetime.timedelta(days=30)
        FirearmsAuthority.objects.create(
            importer=self.importer,
            issuing_constabulary=self.cheshire,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            reference="12/A/D/0001",
        )
        mock_get_importer_details.return_value = []
        send_authority_expiring_firearms_email_task.delay()
        assert mock_get_importer_details.called is True
        assert mock_send_email.called is False

    @freezegun.freeze_time("2020-02-16 12:00:00")
    @mock.patch("web.mail.tasks.send_authority_expiring_firearms_email")
    @mock.patch("web.mail.tasks.get_expiring_importers_details")
    def test_send_authority_expiring_firearms_email_task(
        self, mock_get_importer_details, mock_send_email
    ):
        importers = [ImporterDetails(id=1, name="Importer 1", authority_refs="12345,67890")]
        FirearmsAuthority.objects.create(
            importer=self.importer,
            issuing_constabulary=self.derbyshire,
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True,
            reference="11/A/D/0001",
        )
        FirearmsAuthority.objects.create(
            importer=self.importer,
            issuing_constabulary=self.cheshire,
            start_date=self.start_date,
            end_date=self.end_date,
            is_active=True,
            reference="12/A/D/0001",
        )
        mock_get_importer_details.return_value = importers
        send_authority_expiring_firearms_email_task.delay()
        assert mock_get_importer_details.called is True
        assert mock_send_email.call_count == 2
        mock_send_email.assert_any_call(importers, datetime.date(2020, 3, 17), self.cheshire)
        mock_send_email.assert_any_call(importers, datetime.date(2020, 3, 17), self.derbyshire)
