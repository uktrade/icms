from django.test import TestCase

from web.domains.case.access.models import AccessRequest


class AccessRequesModelsTest(TestCase):
    def test_requester_type(self):
        expected_results = {
            AccessRequest.IMPORTER: 'importer',
            AccessRequest.IMPORTER_AGENT: 'importer',
            AccessRequest.EXPORTER: 'exporter',
            AccessRequest.EXPORTER_AGENT: 'exporter',
        }
        access_request = AccessRequest()
        for k, v in expected_results.items():
            access_request.request_type = k
            self.assertEqual(access_request.requester_type, v)
