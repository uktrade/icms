import factory.fuzzy

from web.domains.case.export.models import CFSProduct


class CFSProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CFSProduct
