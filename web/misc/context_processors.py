from django.conf import settings
from django.http import HttpRequest

from web.sites import SiteName


def header_colour(request: HttpRequest) -> dict[str, str]:
    """Add the required header colour to the context."""
    header_colours = {
        SiteName.IMPORTER: "green",
        SiteName.EXPORTER: "grey",
        SiteName.CASEWORKER: "red",
    }

    return {
        "CHANGE_HEADER_COLOUR": settings.APP_ENV != "production",
        "HEADER_COLOUR": header_colours[request.site.name],
    }
