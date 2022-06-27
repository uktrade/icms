import logging
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand

from web.domains.chief import types as chief_types
from web.domains.chief.client import make_request, request_license

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """Run with the following command: `make manage COMMAND="query_icms_hmrc"`"""
        self.stdout.write("*" * 160)
        self.stdout.write("CHIEF healthcheck url")
        hawk_sender, response = make_request("GET", f"{settings.ICMS_HMRC_DOMAIN}healthcheck/")
        response.raise_for_status()
        self.stdout.write(f"Response status code: {response.status_code}")
        self.stdout.write(f"Response response content: {response.content!r}")

        self.stdout.write("*" * 160)
        self.stdout.write("CHIEF update licence url")
        payload = self.get_sample_request()
        response = request_license(payload)
        self.stdout.write(f"Response status code: {response.status_code}")
        self.stdout.write(f"Response response content: {response.json()}")

        self.stdout.write("*" * 160)
        self.stdout.write("CHIEF trigger send email task")
        hawk_sender, response = make_request(
            "GET", f"{settings.ICMS_HMRC_DOMAIN}mail/send-licence-updates-to-hmrc/"
        )
        self.stdout.write(f"response status code: {response.status_code}")
        self.stdout.write(f"response response content: {response.content!r}")

        self.stdout.write("*" * 160)
        self.stdout.write("CHIEF get licence mail details")
        hawk_sender, response = make_request(
            "GET", f"{settings.ICMS_HMRC_DOMAIN}mail/licence/", params={"id": "GBOIL9089667C"}
        )
        self.stdout.write(f"Response status code: {response.status_code}")
        self.stdout.write(f"Response response content: {response.content!r}")

    def get_sample_request(self) -> chief_types.CreateLicenceData:
        data = {
            "type": "OIL",
            "action": "insert",
            "id": str(uuid.uuid4()),
            "reference": "GBOIL9089667C",
            "case_reference": "IMA/2022/00001",
            "start_date": "2022-06-06",
            "end_date": "2025-05-30",
            "organisation": {
                "eori_number": "112233445566",
                "name": "org name",
                "address": {
                    "line_1": "line_1",
                    "line_2": "line_2",
                    "line_3": "line_3",
                    "line_4": "line_4",
                    "line_5": "line_5",
                    "postcode": "S118ZZ",  # /PS-IGNORE
                },
            },
            "country_group": "G001",
            "restrictions": "Some restrictions.\n\n Some more restrictions",
            "goods": [
                {
                    "description": (
                        "Firearms, component parts thereof, or ammunition of"
                        " any applicable commodity code, other than those"
                        " falling under Section 5 of the Firearms Act 1968"
                        " as amended."
                    ),
                }
            ],
        }

        payload = chief_types.CreateLicenceData(**{"licence": data})

        return payload
