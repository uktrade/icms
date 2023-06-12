import pytest


class AuthTestCase:
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        importer_one_contact,
        importer_two_contact,
        importer,
        office,
        agent_importer,
        ilb_admin_user,
        ilb_admin_client,
        exporter_one_contact,
        exporter,
        exporter_office,
        agent_exporter,
        client,
        importer_client,
        exporter_client,
    ):
        self.importer = importer
        self.importer_office = office
        self.importer_user = importer_one_contact
        self.importer_two_user = importer_two_contact
        self.importer_agent = agent_importer
        self.exporter = exporter
        self.exporter_office = exporter_office
        self.exporter_user = exporter_one_contact
        self.exporter_agent = agent_exporter
        self.ilb_admin_user = ilb_admin_user

        self.anonymous_client = client
        self.exporter_client = exporter_client
        self.importer_client = importer_client
        self.ilb_admin_client = ilb_admin_client
