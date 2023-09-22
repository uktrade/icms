from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from pydantic import AnyHttpUrl, BaseModel, Extra

from web.sites import CASEWORKER_SITE_NAME, EXPORTER_SITE_NAME, IMPORTER_SITE_NAME


class CmdArgs(BaseModel):
    class Config:
        # Ignore extra django command arguments
        extra = Extra.allow

    caseworker_url: AnyHttpUrl
    exporter_url: AnyHttpUrl
    importer_url: AnyHttpUrl


class Command(BaseCommand):
    help = "Configure sites required to run ICMS."

    def add_arguments(self, parser):
        parser.add_argument("caseworker_url")
        parser.add_argument("exporter_url")
        parser.add_argument("importer_url")

    def handle(self, *args, **options) -> None:
        cmd_args = CmdArgs(**options)

        site = Site.objects.get(name=CASEWORKER_SITE_NAME)
        site.domain = get_site_domain(cmd_args.caseworker_url)
        site.save()

        site = Site.objects.get(name=EXPORTER_SITE_NAME)
        site.domain = get_site_domain(cmd_args.exporter_url)
        site.save()

        site = Site.objects.get(name=IMPORTER_SITE_NAME)
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

    if url.port:
        return f"{url.host}:{url.port}"

    return url.host  # type: ignore[return-value]
