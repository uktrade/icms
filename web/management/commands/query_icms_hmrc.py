import logging
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand

from web.domains.chief.client import make_request, request_license

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """Run with the following command: `make manage COMMAND="query_icms_hmrc"`"""

        # Debug logging by default - It's rather noisy!
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.INFO)

        self.stdout.write("CHIEF healthcheck url")
        hawk_sender, response = make_request("GET", f"{settings.ICMS_HMRC_DOMAIN}healthcheck/")
        response.raise_for_status()
        self.stdout.write(f"healthcheck status code: {response.status_code}")
        self.stdout.write(f"healthcheck response content: {response.content!r}")

        self.stdout.write("CHIEF update licence url")
        data: dict[str, Any] = {}
        response = request_license(data, check_response=False)
        self.stdout.write(f"update-licence status code: {response.status_code}")
        self.stdout.write(f"update-licence response content: {response.json()}")
