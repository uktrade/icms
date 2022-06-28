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
        self.stdout.write("CHIEF update licence url (FA-OIL)")
        payload = get_sample_fa_oil_request()
        response = request_license(payload)
        self.stdout.write(f"Response status code: {response.status_code}")
        self.stdout.write(f"Response response content: {response.json()}")

        self.stdout.write("*" * 160)
        self.stdout.write("CHIEF update licence url (FA-DFL)")
        payload = get_sample_fa_dfl_request()
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


def get_sample_fa_oil_request() -> chief_types.CreateLicenceData:
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


def get_sample_fa_dfl_request() -> chief_types.CreateLicenceData:
    data = {
        "type": "DFL",
        "action": "insert",
        "id": str(uuid.uuid4()),
        "reference": "GBSIL9089277C",
        "case_reference": "IMA/2022/00002",
        "start_date": "2022-01-14",
        "end_date": "2022-07-14",
        "organisation": {
            "eori_number": "665544332211",
            "name": "DFL Organisation",
            "address": {
                "line_1": "line_1",
                "line_2": "line_2",
                "line_3": "line_3",
                "line_4": "line_4",
                "line_5": "",
                "postcode": "S881ZZ",  # /PS-IGNORE
            },
        },
        "country_code": "US",
        "restrictions": (
            "Not valid for items originating in or consigned from Iran, North"
            " Korea, Libya, Syria or the Russian Federation.(including any"
            " previous name by which these territories have been known)."
        ),
        "goods": [
            {
                "description": "Penn Arms 40mm multi shot launcher Model PGL6-40LR. serial No PGR 123"
            },
            {"description": "Penn Arms 40 mm single shot launcher serial No GSC 1234"},
        ],
    }

    payload = chief_types.CreateLicenceData(**{"licence": data})

    return payload
