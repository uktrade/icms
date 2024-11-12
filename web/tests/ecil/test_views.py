from http import HTTPStatus

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse


class TestGDSTestPage:
    @pytest.fixture(autouse=True)
    def setup(self, ilb_admin_client, ilb_admin_user):
        self.url = reverse("ecil:gds_example")
        self.client = ilb_admin_client
        self.user = ilb_admin_user

    def test_permission(self, ilb_admin_user):
        url = reverse("ecil:gds_example")

        response = self.client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        self.user.groups.add(Group.objects.get(name="ECIL Prototype User"))

        response = self.client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_get_only(self):
        self.user.groups.add(Group.objects.get(name="ECIL Prototype User"))
        response = self.client.post(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
