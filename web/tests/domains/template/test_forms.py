from django.test import TestCase

from web.domains.template.forms import (
    EmailTemplateForm,
    EndorsementTemplateForm,
    TemplatesFilter,
)
from web.domains.template.models import Template

from .factory import TemplateFactory


class TemplatesFilterTest(TestCase):
    def setUp(self):
        TemplateFactory(
            template_name="Archived Endorsement",
            template_type=Template.ENDORSEMENT,
            template_title="Endorsement Title",
            template_content="This is a test endorsement template",
            application_domain=Template.IMPORT_APPLICATION,
            is_active=False,
        )
        TemplateFactory(
            template_name="Active Letter Template",
            template_type=Template.LETTER_TEMPLATE,
            template_title="Letter Title",
            template_content="This is a test letter template",
            application_domain=Template.IMPORT_APPLICATION,
            is_active=True,
        )
        TemplateFactory(
            template_name="Active Email Template",
            template_title="Email Title",
            template_content="This is a test email template",
            template_type=Template.EMAIL_TEMPLATE,
            application_domain=Template.CERTIFICATE_APPLICATION,
            is_active=True,
        )

    def run_filter(self, data=None):
        return TemplatesFilter(data=data).qs

    def test_template_name_filter(self):
        results = self.run_filter({"template_name": "Active"})
        self.assertEqual(results.count(), 2)

    def test_template_type_filter(self):
        results = self.run_filter({"template_type": Template.EMAIL_TEMPLATE})
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().template_name, "Active Email Template")

    def test_application_domain_filter(self):
        results = self.run_filter({"application_domain": Template.IMPORT_APPLICATION})
        self.assertEqual(results.count(), 2)

    def test_template_title_filter(self):
        results = self.run_filter({"template_title": "endors"})
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().template_title, "Endorsement Title")

    def test_template_content_filter(self):
        results = self.run_filter({"template_content": "er"})
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().template_name, "Active Letter Template")


class EmailTemplateFormTest(TestCase):
    def test_form_valid(self):
        form = EmailTemplateForm(
            data={
                "template_title": "Test Title",
                "template_name": "Test Template",
                "template_content": "Test Content",
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = EmailTemplateForm(
            data={
                "template_name": "Test Email template",
            }
        )
        self.assertFalse(form.is_valid())

    def test_invalid_form_message(self):
        form = EmailTemplateForm(
            data={
                "template_name": "Test Name",
                "template_content": "Test Content",
            }
        )
        self.assertEqual(len(form.errors), 1)
        message = form.errors["template_title"][0]
        self.assertEqual(message, "You must enter this item")


class EndorsementCreateFormTest(TestCase):
    def test_form_valid(self):
        form = EndorsementTemplateForm(
            data={"template_name": "Test Endorsement", "template_content": "Just testing"}
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = EndorsementTemplateForm(
            data={
                "template_name": "Test Endorsement",
            }
        )
        self.assertFalse(form.is_valid())

    def test_invalid_form_message(self):
        form = EndorsementTemplateForm(
            data={
                "template_content": "Test Content",
            }
        )
        self.assertEqual(len(form.errors), 1)
        message = form.errors["template_name"][0]
        self.assertEqual(message, "You must enter this item")
