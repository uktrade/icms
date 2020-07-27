"""Generic sample viewflow object factories.

    Use this for non-process specific tests.

    For actual flows create task and process factories.

    see: web.tests.domains.case.access.factory for examples
    some code adapted from: https://github.com/darahsten/unittest_viewflow"""
import factory
from viewflow import flow
from viewflow.base import Flow, this
from viewflow.models import Process, Task
from viewflow.flow.views import UpdateProcessView


from web.viewflow.nodes import View


class SampleFlow(Flow):
    start = flow.Start().Next(this.task_1)

    task_1 = View(UpdateProcessView).Next(this.task_2)

    task_2 = View(UpdateProcessView).Next(this.end)

    end = flow.End()


class SampleProcessFactory(factory.django.DjangoModelFactory):
    """Creates a sample process for use in tests."""

    class Meta:
        model = Process

    flow_class = SampleFlow


class TaskFactory(factory.django.DjangoModelFactory):
    """Create a sample flow task. Assigns task to owner if set."""

    class Meta:
        model = Task

    process = factory.SubFactory(SampleProcessFactory)
    flow_task = SampleFlow.start
    owner = None
    token = "start"

    @factory.post_generation
    def run_activation(self, create, extracted, **kwargs):
        activation = self.activate()
        if self.owner:
            activation.assign(self.owner)
