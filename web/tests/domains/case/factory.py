import factory
from web.domains.case.models import FurtherInformationRequest
from web.tests.domains.user.factory import UserFactory


class FurtherInformationRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FurtherInformationRequest

    requested_by = factory.SubFactory(UserFactory)
