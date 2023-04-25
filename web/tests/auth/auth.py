import logging

import pytest

from web.tests.helpers import get_test_client

logger = logging.getLogger(__name__)


class AuthTestCase:
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        importer_one_main_contact,
        importer,
        office,
        test_icms_admin_user,
        icms_admin_client,
        exporter_one_main_contact,
        exporter,
        client,
    ):
        self.importer = importer
        self.importer_office = office
        self.importer_user = importer_one_main_contact
        self.exporter = exporter
        self.exporter_user = exporter_one_main_contact
        self.ilb_admin_user = test_icms_admin_user

        self.exporter_client = get_test_client(self.exporter_user)
        self.importer_client = get_test_client(self.importer_user)
        self.ilb_admin_client = icms_admin_client
        self.anonymous_client = client
