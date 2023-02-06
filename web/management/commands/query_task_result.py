from django.core.management.base import BaseCommand
from django_celery_results.models import TaskResult


class Command(BaseCommand):
    help = """Query celery task results. For development use only."""

    def handle(self, *args, **kwargs):
        task_results = TaskResult.objects.all()

        self.stdout.write(f"Task results count: {task_results.count()}")

        for task in task_results:
            print(task.task_name)
