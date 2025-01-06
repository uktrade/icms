from django.conf import settings
from django.http import HttpRequest

from web.sites import SiteName


def environment_information(request: HttpRequest) -> dict[str, str]:
    """Add the current environment & branch to the context."""
    header_colours = {
        SiteName.IMPORTER: "green",
        SiteName.EXPORTER: "grey",
        SiteName.CASEWORKER: "red",
    }

    return {
        "CURRENT_ENVIRONMENT": settings.CURRENT_ENVIRONMENT,
        "CURRENT_BRANCH": settings.CURRENT_BRANCH,
        "CURRENT_TAG": settings.CURRENT_TAG,
        "SHOW_ENVIRONMENT_INFO": settings.CURRENT_ENVIRONMENT != "prod",
        "HEADER_COLOUR": header_colours[request.site.name],
    }
