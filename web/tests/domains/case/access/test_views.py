from django.test import TestCase

from web.domains.case.access.models import AccessRequest
from web.domains.case.access.views import clean_extra_request_data


def populate_fields(access_request):
    access_request.agent_name = 'Agent Smith'
    access_request.agent_address = '50 VS'
    access_request.request_reason = 'Import/Export'


class AccessRequestViewsTest(TestCase):
    def test_missing_request_type(self):
        access_request = AccessRequest()
        self.assertRaises(ValueError, clean_extra_request_data, access_request)

    def test_unknown_request_type(self):
        access_request = AccessRequest()
        access_request.request_type = "ADMIN_ACCESS"
        self.assertRaises(ValueError, clean_extra_request_data, access_request)

    def test_importer(self):
        access_request = AccessRequest()
        access_request.request_type = AccessRequest.IMPORTER
        populate_fields(access_request)

        clean_extra_request_data(access_request)

        self.assertIsNone(access_request.agent_name)
        self.assertIsNone(access_request.agent_address)

    def test_exporter(self):
        access_request = AccessRequest()
        access_request.request_type = AccessRequest.EXPORTER
        populate_fields(access_request)

        clean_extra_request_data(access_request)

        self.assertIsNone(access_request.request_reason)
        self.assertIsNone(access_request.agent_name)
        self.assertIsNone(access_request.agent_address)

    def test_exporter_agent(self):
        access_request = AccessRequest()
        access_request.request_type = AccessRequest.EXPORTER_AGENT
        populate_fields(access_request)

        clean_extra_request_data(access_request)

        self.assertIsNone(access_request.request_reason)
