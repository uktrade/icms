from django.test import TestCase

from web.domains.template.forms import (
    EmailTemplateForm,
    EndorsementTemplateForm,
    LetterTemplateForm,
    TemplatesFilter,
)
from web.models import Template

from .factory import TemplateFactory


class TestTemplatesFilter(TestCase):
    def setUp(self):
        self.archived_endorsement = TemplateFactory(
            template_name="Archived Endorsement",
            template_type=Template.ENDORSEMENT,
            template_title="Endorsement Title",
            template_content="This is a test endorsement template",
            application_domain=Template.IMPORT_APPLICATION,
            is_active=False,
        )
        self.letter = TemplateFactory(
            template_name="Active Letter Template",
            template_type=Template.LETTER_TEMPLATE,
            template_title="Letter Title",
            template_content="This is a test letter template",
            application_domain=Template.IMPORT_APPLICATION,
            is_active=True,
        )
        self.email = TemplateFactory(
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
        results = self.run_filter({"template_name_title": "Active"})
        assert results.count() == 2

    def test_application_domain_filter(self):
        results = self.run_filter({"application_domain": Template.IMPORT_APPLICATION})
        assert self.letter in results
        assert self.archived_endorsement in results

    def test_template_content_filter(self):
        results = self.run_filter({"template_content": "test let"})
        assert results.count() == 1
        assert results.first().template_name == "Active Letter Template"

    def test_filter_name_title(self):
        """Tests that the template_name_title filter searches on both"""
        template_object = TemplateFactory(template_name="weird_name", template_title="weird_title")
        results = self.run_filter({"template_name_title": "weird_name"})

        assert results.count() == 1
        assert results.get() == template_object

        results = self.run_filter({"template_name_title": "weird_title"})
        assert results.count() == 1
        assert results.get() == template_object


class TestEmailTemplateForm(TestCase):
    def test_form_valid(self):
        form = EmailTemplateForm(
            data={
                "template_title": "Test Title",
                "template_name": "Test Template",
                "template_content": "Test Content",
            }
        )
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = EmailTemplateForm(
            data={
                "template_name": "Test Email template",
            }
        )
        assert form.is_valid() is False

    def test_invalid_form_message(self):
        form = EmailTemplateForm(
            data={
                "template_name": "Test Name",
                "template_content": "Test Content",
            }
        )
        assert len(form.errors) == 1
        message = form.errors["template_title"][0]
        assert message == "You must enter this item"


class TestEndorsementCreateForm(TestCase):
    def test_form_valid(self):
        form = EndorsementTemplateForm(
            data={"template_name": "Test Endorsement", "template_content": "Just testing"}
        )
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = EndorsementTemplateForm(
            data={
                "template_name": "Test Endorsement",
            }
        )
        assert form.is_valid() is False

    def test_invalid_form_message(self):
        form = EndorsementTemplateForm(
            data={
                "template_content": "Test Content",
            }
        )
        assert len(form.errors) == 1
        message = form.errors["template_name"][0]
        assert message == "You must enter this item"


def test_letter_template_form_valid():
    form = LetterTemplateForm(
        {
            "template_name": "New Template",
            "template_content": "Test cover letter [[LICENCE_NUMBER]]",
        }
    )
    assert form.is_valid() is True


def test_cover_letter_form_invalid():
    form = LetterTemplateForm(
        {"template_name": "New Template", "template_content": "Test cover letter [[INVALID]]"}
    )
    assert form.is_valid() is False

    error_message = form.errors["template_content"][0]
    assert error_message == "The following placeholders are invalid: [[INVALID]]"
