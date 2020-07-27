from django.test import TestCase

from web.domains.case.fir import forms
from web.tests.domains.user.factory import UserFactory


class FurtherInformationRequestFormTest(TestCase):
    def test_form_valid(self):
        form = forms.FurtherInformationRequestForm(
            data={
                "request_subject": "Testing",
                "request_detail": """
                    Hello, I am testing Further Information Requests.
                    No further information necessary
                """,
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid_without_request_subject(self):
        form = forms.FurtherInformationRequestForm(data={"request_detail": "Test"})
        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors) == 1)
        message = form.errors["request_subject"][0]
        self.assertEqual(message, "You must enter this item")

    def test_form_invalid_without_request_detail(self):
        form = forms.FurtherInformationRequestForm(data={"request_subject": "Test"})
        self.assertEqual(len(form.errors), 1)
        message = form.errors["request_detail"][0]
        self.assertEqual(message, "You must enter this item")


class FurtherInformationRequestResponseFormTest(TestCase):
    def test_form_valid(self):
        response_by = UserFactory()
        form = forms.FurtherInformationRequestResponseForm(
            response_by, data={"response_detail": "here is my response, cheers!",}
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid_without_response_detail(self):
        response_by = UserFactory()
        form = forms.FurtherInformationRequestResponseForm(response_by, data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        message = form.errors["response_detail"][0]
        self.assertEqual(message, "You must enter this item")
