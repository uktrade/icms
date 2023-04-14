from django.test import TestCase

from web.domains.case.fir import forms


class TestFurtherInformationRequestForm(TestCase):
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
        assert form.is_valid(), form.errors

    def test_form_invalid_without_request_subject(self):
        form = forms.FurtherInformationRequestForm(
            data={"request_detail": "Test", "status": "DRAFT"},
            initial={"status": "DRAFT"},
        )
        assert form.is_valid() is False
        assert len(form.errors) == 1

        message = form.errors["request_subject"][0]
        assert message == "You must enter this item"

    def test_form_invalid_without_request_detail(self):
        form = forms.FurtherInformationRequestForm(
            data={"request_subject": "Test"},
            initial={"status": "DRAFT"},
        )
        assert len(form.errors) == 1, form.errors
        message = form.errors["request_detail"][0]
        assert message == "You must enter this item"


class TestFurtherInformationRequestResponseForm(TestCase):
    def test_form_valid(self):
        form = forms.FurtherInformationRequestResponseForm(
            data={
                "response_detail": "here is my response, cheers!",
            }
        )
        assert form.is_valid() is True

    def test_form_invalid_without_response_detail(self):
        form = forms.FurtherInformationRequestResponseForm(data={})
        assert form.is_valid() is False
        assert len(form.errors) == 1
        message = form.errors["response_detail"][0]
        assert message == "You must enter this item"
