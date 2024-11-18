from http import HTTPStatus

import pytest
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse


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
