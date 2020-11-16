import factory
from django.utils import timezone
from viewflow.activation import STATUS
from viewflow.models import Task

from web.domains.case.fir.models import FurtherInformationRequest
from web.tests.domains.user.factory import UserFactory


def _owner_permission(task):
    if hasattr(task.flow_task, "_owner_permission"):
        return task.flow_task._owner_permission


class FurtherInformationRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FurtherInformationRequest

    requested_by = factory.SubFactory(UserFactory)
    is_active = True
    status = factory.fuzzy.FuzzyChoice(FurtherInformationRequest.STATUSES, getter=lambda s: s[0])
    request_subject = factory.Faker("sentence", nb_words=3)
    request_detail = factory.Faker("sentence", nb_words=8)
    email_cc_address_list = None
    requested_datetime = timezone.now()
    response_detail = factory.Faker("sentence", nb_words=6)
    response_datetime = None
    requested_by = None
    response_by = None
    closed_datetime = None
    closed_by = None
    deleted_datetime = None
    deleted_by = None


class FurtherInformationRequestTaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    owner = None
    status = STATUS.NEW
    owner_permission = factory.LazyAttribute(_owner_permission)
    token = "start"

    @factory.post_generation
    def run_activation(self, create, extracted, **kwargs):
        activation = self.activate()
        # Only View tasks can be assigned, other node types are not assined to a human
        if self.owner and hasattr(activation, "assign"):
            activation.assign(self.owner)
