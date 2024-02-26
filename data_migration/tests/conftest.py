import pytest
from django.test import override_settings


@pytest.fixture
def dummy_dm_settings():
    with override_settings(
        ALLOW_DATA_MIGRATION=True,
        ICMS_PROD_USER="TestUser",
        ICMS_PROD_PASSWORD="1234",
    ):
        yield None
