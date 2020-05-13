from django.test import TestCase
from web.domains.template.models import Template


class TemplateTest(TestCase):
    def create_template(self,
                        template_name='Test Template',
                        is_active=True,
                        template_type=Template.ENDORSEMENT,
                        application_domain=Template.IMPORT_APPLICATION):
        return Template.objects.create(template_name=template_name,
                                       is_active=is_active,
                                       template_type=template_type,
                                       application_domain=application_domain)

    def test_create_template(self):
        template = self.create_template()
        self.assertTrue(isinstance(template, Template))
        self.assertEqual(template.template_name, 'Test Template')
        self.assertEqual(template.template_type, Template.ENDORSEMENT)
        self.assertTrue(template.is_active)

    def test_archive_template(self):
        template = self.create_template()
        template.archive()
        self.assertFalse(template.is_active)

    def test_unarchive_template(self):
        template = self.create_template(is_active=False)
        self.assertFalse(template.is_active)
        template.unarchive()
        self.assertTrue(template.is_active)

    def test_string_representation(self):
        product_legisation = self.create_template()
        self.assertEqual(product_legisation.__str__(),
                         'Template - Test Template')
