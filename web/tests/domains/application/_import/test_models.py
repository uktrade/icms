from django.test import TestCase
from web.domains.application._import.models import (ImportApplication,
                                                    ImportApplicationType)
from web.tests.domains.template.factory import TemplateFactory


class ImportApplicationTypeTest(TestCase):
    def create_application_type(self):
        return ImportApplicationType.objects.create(
            is_active=True,
            type_code='TEST',
            type='TEST',
            sub_type_code='TEST',
            sub_type='TEST',
            licence_type_code='TEST',
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
            declaration_template=TemplateFactory(is_active=True))

    def test_create_application_type(self):
        application_type = self.create_application_type()
        self.assertTrue(isinstance(application_type, ImportApplicationType))
        self.assertEqual(application_type.type_code, 'TEST')
        self.assertEqual(application_type.sub_type_code, 'TEST')

    def test_string_representation(self):
        application_type = self.create_application_type()
        self.assertEqual(
            application_type.__str__(),
            f'{application_type.type} ({application_type.sub_type})')
