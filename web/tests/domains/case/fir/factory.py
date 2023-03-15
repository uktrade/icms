import factory
from django.utils import timezone

from web.models import FurtherInformationRequest
from web.tests.domains.user.factory import UserFactory


def _owner_permission(task):
    if hasattr(task.flow_task, "_owner_permission"):
        return task.flow_task._owner_permission


class FurtherInformationRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FurtherInformationRequest

    process_type = FurtherInformationRequest.PROCESS_TYPE
    requested_by = factory.SubFactory(UserFactory)
    is_active = True
    status = FurtherInformationRequest.OPEN
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
