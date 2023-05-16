import pytest


class AuthTestCase:
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        importer_one_contact,
        importer,
        office,
        ilb_admin_user,
        ilb_admin_client,
        exporter_one_contact,
        exporter,
        exporter_office,
        client,
        importer_client,
        exporter_client,
    ):
        self.importer = importer
        self.importer_office = office
        self.importer_user = importer_one_contact
        self.exporter = exporter
        self.exporter_office = exporter_office
        self.exporter_user = exporter_one_contact
        self.ilb_admin_user = ilb_admin_user

        self.anonymous_client = client
        self.exporter_client = exporter_client
        self.importer_client = importer_client
        self.ilb_admin_client = ilb_admin_client
