import pytest


class AuthTestCase:
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        importer_one_contact,
        importer_two_contact,
        importer_one_agent_one_contact,
        importer,
        importer_two,
        office,
        agent_importer,
        ilb_admin_user,
        ilb_admin_two,
        ilb_admin_client,
        ilb_admin_two_client,
        san_admin_user,
        exporter_one_contact,
        exporter_two_contact,
        exporter_one_agent_one_contact,
        exporter,
        exporter_office,
        agent_exporter,
        client,
        importer_client,
        importer_agent_client,
        exporter_client,
        exporter_agent_client,
        exporter_two_client,
        cw_client,
        san_admin_client,
    ):
        self.importer = importer
        self.importer_two = importer_two
        self.importer_office = office
        self.importer_user = importer_one_contact
        self.importer_two_user = importer_two_contact
        self.importer_agent_user = importer_one_agent_one_contact
        self.importer_agent = agent_importer
        self.exporter = exporter
        self.exporter_office = exporter_office
        self.exporter_user = exporter_one_contact
        self.exporter_two_user = exporter_two_contact
        self.exporter_agent_user = exporter_one_agent_one_contact
        self.exporter_agent = agent_exporter
        self.ilb_admin_user = ilb_admin_user
        self.ilb_admin_two_user = ilb_admin_two
        self.san_admin_user = san_admin_user

        self.anonymous_client = cw_client
        self.exporter_client = exporter_client
        self.exporter_agent_client = exporter_agent_client
        self.exporter_two_client = exporter_two_client
        self.importer_client = importer_client
        self.importer_agent_client = importer_agent_client
        self.ilb_admin_client = ilb_admin_client
        self.ilb_admin_two_client = ilb_admin_two_client
        self.san_admin_client = san_admin_client
