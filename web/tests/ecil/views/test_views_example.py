from http import HTTPStatus

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from pytest_django.asserts import assertInHTML

from web.models import Commodity, ECILExample, ECILMultiStepExample


class TestGDSTestPageView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client):
        self.url = reverse("ecil:example:gds_example")
        self.client = prototype_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get_only(self):
        response = self.client.post(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestGDSFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client):
        self.url = reverse("ecil:example:gds_form_example")
        self.client = prototype_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post(self):
        form_data = {
            "text_input_field": "valid test val",
            "text": "",
            "text_two": "value",
            "text_three": "",
            "radio_input_field": "text_two",
            "character_count_field": "value",
            "checkbox_field": ["carcasses", "mines", "farm"],
            "date_input_field_0": "23",
            "date_input_field_1": "7",
            "date_input_field_2": "2022",
            "file_upload_field": SimpleUploadedFile("example.png", b"file_content"),
            "password_field": "value",
            "select_field": "published",
            "autocomplete_select": "1",
            "textarea_field": "value",
        }
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND


class TestGDSModelFormCreateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client):
        self.url = reverse("ecil:example:gds_model_form_example")
        self.client = prototype_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post(self):

        assert ECILExample.objects.count() == 0

        valid_commodity = Commodity.objects.filter(commodity_code__startswith="500500").first()

        form_data = {
            "big_integer_field": -12345,
            "boolean_field": True,
            "optional_boolean_field": False,
            "char_field": "value",
            "char_choice_field": ECILExample.PrimaryColours.blue,
            "optional_char_field": "",
            "date_field_0": "23",
            "date_field_1": "7",
            "date_field_2": "2022",
            "decimal_field": "123.45",
            "email_field": "email@example.com",  # /PS-IGNORE
            "float_field": 532.21,
            "integer_field": -12345,
            "positive_big_integer_field": 12345,
            "positive_integer_field": 12345,
            "positive_small_integer_field": 1,
            "slug_field": "slugs",
            "small_integer_field": -1,
            "text_field": "Some text",
            "foreign_key_field": valid_commodity.pk,
        }
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        assert ECILExample.objects.count() == 1
        assert response.url == reverse("ecil:example:ecil_example_list")

        # Check the list view shows the new record
        response = self.client.get(response.url)
        assert response.status_code == HTTPStatus.OK
        assert response.context["object_list"].count() == 1
        assert response.context["object_list"].first() == ECILExample.objects.first()


class TestGDSConditionalModelFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client):
        self.url = reverse("ecil:example:gds_conditional_model_form_example")
        self.client = prototype_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post(self):
        form_data = {
            "blue": "",
            "red": "value",
            "yellow": "",
            "char_choice_field": "red",
        }
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND


class TestECILMultiStepFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client):
        self.client = prototype_client

    def get_url(self, step: str) -> str:
        return reverse("ecil:example:step_form", kwargs={"step": step})

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.get_url("one"))
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.get_url("one"))
        assert response.status_code == HTTPStatus.OK

    def test_post(self):
        response = self.client.post(self.get_url("one"), data={"favourite_colour": "red"})
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == self.get_url("two")

        response = self.client.post(self.get_url("two"), data={"likes_cake": "True"})
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == self.get_url("three")

        response = self.client.post(self.get_url("three"), data={"favourite_book": "The Bible"})
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:example:step_form_summary")

        # Check the summary view actually saves the data
        # This is really a test for TestECILMultiStepFormSummaryView below
        assert ECILMultiStepExample.objects.count() == 0
        response = self.client.post(reverse("ecil:example:step_form_summary"))
        assert response.status_code == HTTPStatus.FOUND
        assert ECILMultiStepExample.objects.count() == 1

        record = ECILMultiStepExample.objects.first()
        assert record.favourite_colour == "red"
        assert record.likes_cake
        assert record.favourite_book == "The Bible"

        # Test the summary redirects to list view and display record
        assert response.url == reverse("ecil:example:multi_step_model_list")
        response = self.client.get(response.url)
        assert response.status_code == HTTPStatus.OK
        assert response.context["object_list"].count() == 1
        assert response.context["object_list"].first() == ECILMultiStepExample.objects.first()


class TestECILMultiStepFormSummaryView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client):
        self.client = prototype_client

        self.url = reverse("ecil:example:step_form_summary")

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        # TODO: Revisit in ECIL-618
        #       Summary screen will not render partially valid data with Pydantic
        response = self.client.get(self.url)
        html = response.content.decode("utf-8")
        assertInHTML("No value entered (Fix in ECIL-618)", html, 3)

    # happy path has been tested above in TestECILMultiStepFormView.
    def test_post_errors(self):
        response = self.client.post(self.url)
        assert response.status_code == HTTPStatus.OK

        form = response.context["form"]
        assert form.errors == {
            "favourite_book": ["You must enter this item"],
            "favourite_colour": ["You must enter this item"],
            "likes_cake": ["You must enter this item"],
        }

        # TODO: Revisit in ECIL-618
        html = response.content.decode("utf-8")
        assertInHTML("No value entered (Fix in ECIL-618)", html, 3)
