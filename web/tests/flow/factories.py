import factory

from web.flow.models import Task


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task
