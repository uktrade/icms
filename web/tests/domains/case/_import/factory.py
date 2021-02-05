import factory
import factory.fuzzy

from web.domains.case._import.models import (
    ImportApplicationType,
    OpenIndividualLicenceApplication,
)
from web.tests.domains.template.factory import TemplateFactory


class ImportApplicationTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ImportApplicationType

    is_active = True
    type = factory.Faker("sentence", nb_words=3)
    sub_type = factory.Faker("sentence", nb_words=2)
    licence_type_code = factory.fuzzy.FuzzyText(length=10)
    sigl_flag = True
    chief_flag = True
    chief_licence_prefix = factory.fuzzy.FuzzyText(length=3)
    paper_licence_flag = True
    electronic_licence_flag = True
    cover_letter_flag = True
    cover_letter_schedule_flag = True
    category_flag = True
    sigl_category_prefix = factory.fuzzy.FuzzyText(length=4)
    chief_category_prefix = factory.fuzzy.FuzzyText(length=2)
    default_licence_length_months = factory.fuzzy.FuzzyInteger(1, 12)
    endorsements_flag = True
    default_commodity_desc = factory.Faker("sentence", nb_words=10)
    quantity_unlimited_flag = True
    exp_cert_upload_flag = True
    supporting_docs_upload_flag = True
    multiple_commodities_flag = True
    licence_category_description = factory.Faker("sentence", nb_words=8)
    usage_auto_category_desc_flag = True
    case_checklist_flag = True
    importer_printable = True
    declaration_template = factory.SubFactory(TemplateFactory, is_active=True)


class OILApplicationTypeFactory(ImportApplicationTypeFactory):
    type = ImportApplicationType.TYPE_FIREARMS_AMMUNITION_CODE
    sub_type = ImportApplicationType.SUBTYPE_OPEN_INDIVIDUAL_LICENCE


class OILApplicationFactory(factory.django.DjangoModelFactory):
    process_type = OpenIndividualLicenceApplication.PROCESS_TYPE
    application_type = factory.SubFactory(OILApplicationTypeFactory)

    class Meta:
        model = OpenIndividualLicenceApplication
