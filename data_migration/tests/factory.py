import random

import factory.fuzzy
from django.utils import timezone

from data_migration import models


class FileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.File

    filename = factory.fuzzy.FuzzyText(length=6)
    content_type = factory.fuzzy.FuzzyText(length=6)
    file_size = random.randint(1, 100000)
    path = factory.fuzzy.FuzzyText(length=6)
    created_datetime = timezone.datetime.now()


class CountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Country

    name = factory.fuzzy.FuzzyText(length=6)
    is_active = random.choice([True, False])
    type = factory.fuzzy.FuzzyText(length=6)
    commission_code = factory.fuzzy.FuzzyText(length=6)
    hmrc_code = factory.fuzzy.FuzzyText(length=6)


class CountryGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.CountryGroup

    country_group_id = factory.fuzzy.FuzzyText(length=6)
    name = factory.fuzzy.FuzzyText(length=6)
    comments = factory.fuzzy.FuzzyText(length=6)


class ImportApplicationTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ImportApplicationType

    is_active = random.choice([True, False])
    type = "WD"
    sub_type = factory.fuzzy.FuzzyText(length=6)
    licence_type_code = factory.fuzzy.FuzzyText(length=6)
    sigl_flag = random.choice(["true", "false"])
    chief_flag = random.choice(["true", "false"])
    chief_licence_prefix = factory.fuzzy.FuzzyText(length=6)
    paper_licence_flag = random.choice(["true", "false"])
    chief_flag = random.choice(["true", "false"])
    electronic_licence_flag = random.choice(["true", "false"])
    cover_letter_flag = random.choice(["true", "false"])
    chief_flag = random.choice(["true", "false"])
    cover_letter_schedule_flag = random.choice(["true", "false"])
    category_flag = random.choice(["true", "false"])
    sigl_category_prefix = factory.fuzzy.FuzzyText(length=6)
    chief_category_prefix = factory.fuzzy.FuzzyText(length=6)
    endorsements_flag = random.choice(["true", "false"])
    default_commodity_desc = factory.fuzzy.FuzzyText(length=6)
    quantity_unlimited_flag = random.choice(["true", "false"])
    unit_list_csv = factory.fuzzy.FuzzyText(length=6)
    exp_cert_upload_flag = random.choice(["true", "false"])
    supporting_docs_upload_flag = random.choice(["true", "false"])
    multiple_commodities_flag = random.choice(["true", "false"])
    guidance_file_url = factory.fuzzy.FuzzyText(length=6)
    licence_category_description = factory.fuzzy.FuzzyText(length=6)
    usage_auto_category_desc_flag = random.choice(["true", "false"])
    case_checklist_flag = random.choice(["true", "false"])
    importer_printable = random.choice(["true", "false"])
    origin_country_group = factory.SubFactory(CountryGroupFactory)
    consignment_country_group = factory.SubFactory(CountryGroupFactory)
    master_country_group = factory.SubFactory(CountryGroupFactory)


class ProcessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Process

    process_type = factory.fuzzy.FuzzyText(length=6)
    is_active = random.choice([True, False])


class ImportApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ImportApplication

    ima = factory.SubFactory(ProcessFactory)
    imad_id = random.randint(1, 100000)
    status = factory.fuzzy.FuzzyText(length=6)
    reference = factory.fuzzy.FuzzyText(length=6)
    create_datetime = timezone.now()
    application_type = factory.SubFactory(ImportApplicationTypeFactory)


class ImportContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ImportContact

    import_application = factory.SubFactory(ImportApplicationFactory)


class OILSupplementaryInfoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.OILSupplementaryInfo

    imad = factory.SubFactory(ImportApplicationFactory)


class OILSupplementaryReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.OILSupplementaryReport

    supplementary_info = factory.SubFactory(OILSupplementaryInfoFactory)


class DFLSupplementaryInfoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DFLSupplementaryInfo

    imad = factory.SubFactory(ImportApplicationFactory)


class DFLGoodsCertificateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DFLGoodsCertificate

    goods_description = factory.fuzzy.FuzzyText(length=6)
    deactivated_certificate_reference = factory.fuzzy.FuzzyText(length=6)


class ConstabularyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Constabulary

    name = factory.fuzzy.FuzzyText(length=6)
    region = factory.fuzzy.FuzzyText(length=3)
    email = factory.fuzzy.FuzzyText(length=6)


class UserImportCertificateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.UserImportCertificate

    target = factory.SubFactory(FileFactory)
    constabulary = factory.SubFactory(ConstabularyFactory)
    reference = factory.fuzzy.FuzzyText(length=6)
    certificate_type = factory.fuzzy.FuzzyText(length=6)
    date_issued = timezone.datetime(2020, 1, 1)
    expiry_date = timezone.datetime(2020, 1, 1)
    updated_datetime = timezone.datetime(2020, 1, 1)
