import random

import factory
import factory.fuzzy

from web.domains.case._import.models import ImportApplicationType
from web.tests.domains.template.factory import TemplateFactory


class ImportApplicationTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ImportApplicationType

    is_active = random.choice([True, False])
    type_code = factory.fuzzy.FuzzyText(length=10)
    type = factory.Faker("sentence", nb_words=3)
    sub_type_code = factory.fuzzy.FuzzyText(length=10)
    sub_type = factory.Faker("sentence", nb_words=2)
    licence_type_code = factory.fuzzy.FuzzyText(length=10)
    sigl_flag = random.choice([True, False])
    chief_flag = random.choice([True, False])
    chief_licence_prefix = factory.fuzzy.FuzzyText(length=3)
    paper_licence_flag = random.choice([True, False])
    electronic_licence_flag = random.choice([True, False])
    cover_letter_flag = random.choice([True, False])
    cover_letter_schedule_flag = random.choice([True, False])
    category_flag = random.choice([True, False])
    sigl_category_prefix = factory.fuzzy.FuzzyText(length=4)
    chief_category_prefix = factory.fuzzy.FuzzyText(length=2)
    default_licence_length_months = factory.fuzzy.FuzzyInteger(1, 12)
    endorsements_flag = random.choice([True, False])
    default_commodity_desc = factory.Faker("sentence", nb_words=10)
    quantity_unlimited_flag = random.choice([True, False])
    exp_cert_upload_flag = random.choice([True, False])
    supporting_docs_upload_flag = random.choice([True, False])
    multiple_commodities_flag = random.choice([True, False])
    licence_category_description = factory.Faker("sentence", nb_words=8)
    usage_auto_category_desc_flag = random.choice([True, False])
    case_checklist_flag = random.choice([True, False])
    importer_printable = random.choice([True, False])
    declaration_template = factory.SubFactory(TemplateFactory, is_active=True)
