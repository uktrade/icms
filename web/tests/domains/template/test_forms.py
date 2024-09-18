from django.test import TestCase

from web.domains.template.forms import (
    EmailTemplateForm,
    EndorsementTemplateForm,
    LetterTemplateForm,
    TemplatesFilter,
)
from web.models import Template


class TestTemplatesFilter(TestCase):
    def setUp(self):
        self.archived_endorsement = Template.objects.filter(
            template_type=Template.ENDORSEMENT,
            application_domain=Template.IMPORT_APPLICATION,
            is_active=False,
        ).first()
        self.letter = Template.objects.filter(
            template_type=Template.LETTER_TEMPLATE,
            application_domain=Template.IMPORT_APPLICATION,
            is_active=True,
        ).first()
        self.email = Template.objects.filter(
            template_type=Template.EMAIL_TEMPLATE,
            application_domain=Template.CERTIFICATE_APPLICATION,
            is_active=True,
        ).first()

    def run_filter(self, data=None):
        return TemplatesFilter(data=data).qs

    def test_template_name_filter(self):
        results = self.run_filter({"template_name_title": "Declaration"})
        assert results.count() == 3

    def test_application_domain_filter(self):
        results = self.run_filter({"application_domain": Template.IMPORT_APPLICATION})
        assert self.letter in results
        assert self.archived_endorsement in results

    def test_filter_name_title(self):
        """Tests that the template_name_title filter searches on both"""
        template_object = Template.objects.get(template_name="General Declaration of Truth")
        results = self.run_filter({"template_name_title": "General Declaration of Truth"})

        assert results.count() == 1
        assert results.get() == template_object

        assert results.count() == 1
        assert results.get() == template_object


class TestEmailTemplateForm(TestCase):
    def test_form_valid(self):
        form = EmailTemplateForm(
            data={
                "template_name": "Test Template",
                "title": "Test Title",
                "content": "Test Content",
            }
        )
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = EmailTemplateForm(
            data={
                "template_name": "Test Email template",
                "content": "Test Content",
            }
        )
        assert form.is_valid() is False


class TestEndorsementCreateForm(TestCase):
    def test_form_valid(self):
        form = EndorsementTemplateForm(
            data={"template_name": "Test Endorsement", "content": "Just testing"}
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
                "content": "Test Content",
            }
        )
        assert len(form.errors) == 1
        message = form.errors["template_name"][0]
        assert message == "You must enter this item"


def test_letter_template_form_valid():
    form = LetterTemplateForm(
        {
            "template_name": "New Template",
            "content": "Test cover letter [[LICENCE_NUMBER]]",
        }
    )
    assert form.is_valid() is True
