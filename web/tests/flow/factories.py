import factory

from web.models import Task


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task
