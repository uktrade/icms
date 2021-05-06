from django.test import TestCase

from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.office.factory import OfficeFactory
from web.tests.domains.template.factory import TemplateFactory
from web.tests.domains.user.factory import UserFactory


class ImportApplicationTypeTest(TestCase):
    def create_application_type(self):
        return ImportApplicationType.objects.create(
            is_active=True,
            type="TEST",
            sub_type="TEST",
            licence_type_code="TEST",
            sigl_flag=True,
            chief_flag=True,
            paper_licence_flag=False,
            electronic_licence_flag=False,
            cover_letter_flag=False,
            cover_letter_schedule_flag=False,
            category_flag=True,
            endorsements_flag=True,
            quantity_unlimited_flag=True,
            exp_cert_upload_flag=False,
            supporting_docs_upload_flag=False,
            multiple_commodities_flag=False,
            usage_auto_category_desc_flag=True,
            case_checklist_flag=True,
            importer_printable=True,
            declaration_template=TemplateFactory(is_active=True),
        )

    def test_create_application_type(self):
        application_type = self.create_application_type()
        self.assertTrue(isinstance(application_type, ImportApplicationType))
        self.assertEqual(application_type.type, "TEST")
        self.assertEqual(application_type.sub_type, "TEST")

    def test_string_representation(self):
        application_type = self.create_application_type()
        self.assertEqual(
            application_type.__str__(), f"{application_type.type} ({application_type.sub_type})"
        )


class ImportApplicationTest(TestCase):
    def create_import_application(self):
        importer = ImporterFactory(
            offices=(OfficeFactory(is_active=True), OfficeFactory(is_active=True))
        )
        return ImportApplication.objects.create(
            is_active=True,
            application_type=ImportApplicationType.objects.get(
                type=ImportApplicationType.Types.SANCTION_ADHOC
            ),
            created_by=UserFactory(is_active=True),
            last_updated_by=UserFactory(is_active=True),
            importer=importer,
            importer_office=importer.offices.first(),
        )

    def test_create_import_application(self):
        application = self.create_import_application()
        self.assertTrue(isinstance(application, ImportApplication))
