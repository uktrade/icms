from django.test import TestCase

from web.models import Template


class TestTemplate(TestCase):
    def create_template(
        self,
        template_name="Test Template",
        is_active=True,
        template_type=Template.ENDORSEMENT,
        application_domain=Template.IMPORT_APPLICATION,
    ):
        return Template.objects.create(
            template_name=template_name,
            is_active=is_active,
            template_type=template_type,
            application_domain=application_domain,
        )

    def test_create_template(self):
        template = self.create_template()
        assert isinstance(template, Template)
        assert template.template_name == "Test Template"
        assert template.template_type == Template.ENDORSEMENT
        assert template.is_active is True

    def test_archive_template(self):
        template = self.create_template()
        template.archive()
        assert template.is_active is False

    def test_unarchive_template(self):
        template = self.create_template(is_active=False)
        assert template.is_active is False
        template.unarchive()
        assert template.is_active is True

    def test_string_representation(self):
        product_legisation = self.create_template()
        assert product_legisation.__str__() == "Template - Test Template"
