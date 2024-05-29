from typing import Any

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from pydantic import AnyHttpUrl, BaseModel, ConfigDict

from web.sites import SiteName


class CmdArgs(BaseModel):
    model_config = ConfigDict(
        # Ignore extra django command arguments
        extra="allow",
    )

    caseworker_url: AnyHttpUrl
    exporter_url: AnyHttpUrl
    importer_url: AnyHttpUrl


class Command(BaseCommand):
    help = "Configure sites required to run ICMS. If no values are specified the values are taken from the environment variables."

    def add_arguments(self, parser):
        parser.add_argument(
            "--caseworker_url",
            dest="caseworker_url",
            type=str,
            required=False,
            default=settings.CASEWORKER_SITE_URL,
        )
        parser.add_argument(
            "--exporter_url",
            dest="exporter_url",
            type=str,
            required=False,
            default=settings.EXPORTER_SITE_URL,
        )
        parser.add_argument(
            "--importer_url",
            dest="importer_url",
            type=str,
            required=False,
            default=settings.IMPORTER_SITE_URL,
        )

    def handle(self, *args: Any, **options: Any) -> None:
        cmd_args = CmdArgs(**options)

        site = Site.objects.get(name=SiteName.CASEWORKER)
        site.domain = get_site_domain(cmd_args.caseworker_url)
        site.save()

        site = Site.objects.get(name=SiteName.EXPORTER)
        site.domain = get_site_domain(cmd_args.exporter_url)
        site.save()

        site = Site.objects.get(name=SiteName.IMPORTER)
        site.domain = get_site_domain(cmd_args.importer_url)
        site.save()


def get_site_domain(url: AnyHttpUrl) -> str:
    """Return a valid site domain from the incoming url.

    get_current_site() is used in every request to work out the correct site.
    It will try to get the current site by comparing Site.domain values with the host name from
    the request.get_host() method.

    This function ensures that will work in all environments.
    e.g. running in docker the port is important
    """

    if settings.APP_ENV in ("local", "test"):
        return f"{url.host}:{url.port}"

    return url.host  # type: ignore[return-value]
