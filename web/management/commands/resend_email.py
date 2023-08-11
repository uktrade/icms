import json
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django_celery_results.models import TaskResult

from web.mail.api import send_email
from web.mail.constants import SEND_EMAIL_TASK_NAME


class Command(BaseCommand):
    help = "Resend an email for a given task result id"

    def add_arguments(self, parser):
        parser.add_argument(
            "--task_id",
            type=UUID,
            help="",
            required=True,
        )

    def get_task(self, task_id: UUID) -> TaskResult:
        return TaskResult.objects.get(task_id=str(task_id), task_name=SEND_EMAIL_TASK_NAME)

    def get_send_mail_args_from_task(self, task: TaskResult) -> tuple:
        json_args = json.loads(task.task_args)
        return eval(json_args)

    def handle(self, *args, **options) -> None:
        self.stdout.write("Resending email")
        try:
            task = self.get_task(options["task_id"])
        except ObjectDoesNotExist:
            self.stdout.write("Error: Task Not found")
        else:
            send_mail_args = self.get_send_mail_args_from_task(task)
            response = send_email(*send_mail_args)
            self.stdout.write(json.dumps(response))
            self.stdout.write("Email sent")
