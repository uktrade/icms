import factory
from django.utils import timezone

from web.models import ApprovalRequest
from web.tests.domains.case.access.factory import AccessRequestFactory
from web.tests.domains.user.factory import UserFactory


class ApprovalRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ApprovalRequest

    access_request = factory.SubFactory(AccessRequestFactory)

    status = factory.fuzzy.FuzzyChoice(ApprovalRequest.STATUSES, getter=lambda s: s[0])
    request_date = timezone.now()
    requested_by = factory.SubFactory(UserFactory, is_active=True)
    requested_from = None
    response = None
    response_by = None
    response_date = None
    response_reason = None
