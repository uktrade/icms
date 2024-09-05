import json
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from web.domains.chief.client import make_request


# To run: make manage args="check_icms_hmrc_connection"
class Command(BaseCommand):
    help = """Test ICMS can send a request to ICMS-HMRC server."""

    def handle(self, *args, **options):
        self.stdout.write("Checking ICMS-HMRC connection.")

        url = urljoin(settings.ICMS_HMRC_DOMAIN, "mail/check-icms-hmrc-connection/")

        data = {"foo": "bar"}
        hawk_sender, response = make_request(
            "POST", url, data=json.dumps(data), headers={"Content-Type": "application/json"}
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            self.stderr.write(str(response.content))
            raise e

        # Verify the response signature.
        server_auth = response.headers["Server-authorization"]
        hawk_sender.accept_response(
            server_auth, content=response.content, content_type=response.headers["Content-type"]
        )

        response_content = json.loads(response.content.decode("utf-8"))

        if response_content != {"bar": "foo"}:
            raise CommandError(f"Invalid response from ICMS-HMRC: {response_content}")

        self.stdout.write("ICMS can communicate with ICMS-HMRC using mohawk.", self.style.SUCCESS)
