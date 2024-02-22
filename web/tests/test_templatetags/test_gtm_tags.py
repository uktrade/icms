from django.conf import settings
from django.test import override_settings

from web.sites import SiteName


def test_site_names_match():
    """Testing that the keys used in the GTM dicts match the actual SiteName choices."""
    assert set(settings.GTM_AUTH_KEYS.keys()) == {each[0] for each in SiteName.choices}
    assert set(settings.GTM_CONTAINER_IDS.keys()) == {each[0] for each in SiteName.choices}
    assert set(settings.GTM_PREVIEW_KEYS.keys()) == {each[0] for each in SiteName.choices}


@override_settings(
    GTM_AUTH_KEYS={"Caseworker": "cw_auth_key"},
    GTM_CONTAINER_IDS={"Caseworker": "cw_container_id"},
    GTM_PREVIEW_KEYS={"Caseworker": "cw_preview_key"},
)
def test_caseworker_tags_rendered_correctly(cw_client):
    response = cw_client.get("", follow=True)
    assert "gtm_auth=cw_auth_key" in response.content.decode("utf-8")
    assert "gtm_preview=cw_preview_key" in response.content.decode("utf-8")
    assert "id=cw_container_id" in response.content.decode("utf-8")


@override_settings(
    GTM_AUTH_KEYS={"Export A Certificate": "export_auth_key"},
    GTM_CONTAINER_IDS={"Export A Certificate": "export_container_id"},
    GTM_PREVIEW_KEYS={"Export A Certificate": "export_preview_key"},
)
def test_export_tags_rendered_correctly(exporter_client):
    response = exporter_client.get("", follow=True)
    assert "gtm_auth=export_auth_key" in response.content.decode("utf-8")
    assert "gtm_preview=export_preview_key" in response.content.decode("utf-8")
    assert "id=export_container_id" in response.content.decode("utf-8")


@override_settings(
    GTM_AUTH_KEYS={"Import A Licence": "import_auth_key"},
    GTM_CONTAINER_IDS={"Import A Licence": "import_container_id"},
    GTM_PREVIEW_KEYS={"Import A Licence": "import_preview_key"},
)
def test_import_tags_rendered_correctly(importer_client):
    response = importer_client.get("", follow=True)
    assert "gtm_auth=import_auth_key" in response.content.decode("utf-8")
    assert "gtm_preview=import_preview_key" in response.content.decode("utf-8")
    assert "id=import_container_id" in response.content.decode("utf-8")
