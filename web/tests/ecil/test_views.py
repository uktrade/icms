from http import HTTPStatus

import pytest
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from web.models import ECILExample


class TestGDSTestPageView:
    @pytest.fixture(autouse=True)
    def setup(self, ilb_admin_client, ilb_admin_user):
        self.url = reverse("ecil:gds_example")
        self.client = ilb_admin_client
        self.user = ilb_admin_user

    def test_permission(self, ilb_admin_user):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        self.user.groups.add(Group.objects.get(name="ECIL Prototype User"))

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get_only(self):
        self.user.groups.add(Group.objects.get(name="ECIL Prototype User"))
        response = self.client.post(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestGDSFormView:
    @pytest.fixture(autouse=True)
    def setup(self, ilb_admin_client, ilb_admin_user):
        self.url = reverse("ecil:gds_form_example")
        self.client = ilb_admin_client
        self.user = ilb_admin_user

    def test_permission(self, ilb_admin_user):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        self.user.groups.add(Group.objects.get(name="ECIL Prototype User"))

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post(self):
        self.user.groups.add(Group.objects.get(name="ECIL Prototype User"))

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
            "textarea_field": "value",
        }
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND


class TestGDSModelFormView:
    @pytest.fixture(autouse=True)
    def setup(self, ilb_admin_client, ilb_admin_user):
        self.url = reverse("ecil:gds_model_form_example")
        self.client = ilb_admin_client
        self.user = ilb_admin_user

    def test_permission(self, ilb_admin_user):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        self.user.groups.add(Group.objects.get(name="ECIL Prototype User"))

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post(self):
        self.user.groups.add(Group.objects.get(name="ECIL Prototype User"))

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
        }
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND


class TestGDSConditionalModelFormView:
    @pytest.fixture(autouse=True)
    def setup(self, ilb_admin_client, ilb_admin_user):
        self.url = reverse("ecil:gds_conditional_model_form_example")
        self.client = ilb_admin_client
        self.user = ilb_admin_user

    def test_permission(self, ilb_admin_user):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        self.user.groups.add(Group.objects.get(name="ECIL Prototype User"))

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post(self):
        self.user.groups.add(Group.objects.get(name="ECIL Prototype User"))
        form_data = {
            "blue": "",
            "red": "value",
            "yellow": "",
            "char_choice_field": "red",
        }
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
