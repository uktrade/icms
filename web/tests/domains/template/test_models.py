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

    def test_string_representation(self):
        product_legisation = self.create_template()
        assert product_legisation.__str__() == "Test Template"


def test_all_template_codes_are_valid(db):
    for template_code in Template.Codes:
        Template.objects.get(template_code=template_code)
