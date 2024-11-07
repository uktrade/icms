import importlib as il
from http import HTTPStatus

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import NoReverseMatch, clear_url_caches, reverse


def reload_urlconf(url_module=settings.ROOT_URLCONF):
    module = il.import_module(url_module)
    il.reload(module)


def test_ilb_admin_client_can_access_private_urls(ilb_admin_client):
    # By default, INCLUDE_PRIVATE_URLS is set to True in settings_test.py
    response = ilb_admin_client.get(reverse("signature-list"))
    assert response.status_code == HTTPStatus.OK


@override_settings(INCLUDE_PRIVATE_URLS=False)
def test_ilb_admin_client_cant_access_private_urls(ilb_admin_client):
    reload_urlconf()
    reload_urlconf("web.urls")
    clear_url_caches()

    # Check we can't use reverse.
    with pytest.raises(NoReverseMatch):
        reverse("signature-list")

    response = ilb_admin_client.get("/signature/")
    assert response.status_code == HTTPStatus.NOT_FOUND
