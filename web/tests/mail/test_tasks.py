from unittest import mock

from celery.result import EagerResult

from web.mail.tasks import send_mailshot_email_task, send_retract_mailshot_email_task


class TestMailTasks:
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
