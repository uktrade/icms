from django.test import TestCase

from web.domains.case.access.models import AccessRequest
from web.domains.case.access.views import clean_extra_request_data


def populate_fields(access_request):
    access_request.agent_name = 'Agent Smith'
    access_request.agent_address = '50 VS'
    access_request.request_reason = 'Import/Export'


class AccessRequestViewsTest(TestCase):
    def testMissingRequestType(self):
        access_request = AccessRequest()
        self.assertRaises(ValueError, clean_extra_request_data, access_request)

    def testUnknownRequestType(self):
        access_request = AccessRequest()
        access_request.request_type = "ADMIN_ACCESS"
        self.assertRaises(ValueError, clean_extra_request_data, access_request)

    def testImporter(self):
        access_request = AccessRequest()
        access_request.request_type = AccessRequest.IMPORTER
        populate_fields(access_request)

        clean_extra_request_data(access_request)

        self.assertIsNone(access_request.agent_name)
        self.assertIsNone(access_request.agent_address)

    def testExporter(self):
        access_request = AccessRequest()
        access_request.request_type = AccessRequest.EXPORTER
        populate_fields(access_request)

        clean_extra_request_data(access_request)

        self.assertIsNone(access_request.request_reason)
        self.assertIsNone(access_request.agent_name)
        self.assertIsNone(access_request.agent_address)

    def testExporterAgent(self):
        access_request = AccessRequest()
        access_request.request_type = AccessRequest.EXPORTER_AGENT
        populate_fields(access_request)

        clean_extra_request_data(access_request)

        self.assertIsNone(access_request.request_reason)
