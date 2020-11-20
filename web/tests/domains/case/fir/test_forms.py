from django.test import TestCase

from web.domains.case.fir import forms


class FurtherInformationRequestFormTest(TestCase):
    def test_form_valid(self):
        form = forms.FurtherInformationRequestForm(
            data={
                "request_subject": "Testing",
                "request_detail": """
                    Hello, I am testing Further Information Requests.
                    No further information necessary
                """,
            },
            initial={"status": "DRAFT"},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_without_request_subject(self):
        form = forms.FurtherInformationRequestForm(
            data={"request_detail": "Test", "status": "DRAFT"}, initial={"status": "DRAFT"},
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors) == 1, form.errors)
        message = form.errors["request_subject"][0]
        self.assertEqual(message, "You must enter this item")

    def test_form_invalid_without_request_detail(self):
        form = forms.FurtherInformationRequestForm(
            data={"request_subject": "Test"}, initial={"status": "DRAFT"},
        )
        self.assertEqual(len(form.errors), 1, form.errors)
        message = form.errors["request_detail"][0]
        self.assertEqual(message, "You must enter this item")


class FurtherInformationRequestResponseFormTest(TestCase):
    def test_form_valid(self):
        form = forms.FurtherInformationRequestResponseForm(
            data={"response_detail": "here is my response, cheers!",}
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid_without_response_detail(self):
        form = forms.FurtherInformationRequestResponseForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        message = form.errors["response_detail"][0]
        self.assertEqual(message, "You must enter this item")
