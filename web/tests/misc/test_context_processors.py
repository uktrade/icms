from django.contrib.sites.models import Site
from django.test import RequestFactory, override_settings

from web.misc.context_processors import header_colour
from web.sites import SiteName


@override_settings(
    APP_ENV="test",
)
def test_environment_information(rf: RequestFactory, db):
    request = rf.request()
    request.site = Site.objects.get(name=SiteName.IMPORTER)
    assert header_colour(request) == {
        "CHANGE_HEADER_COLOUR": True,
        "HEADER_COLOUR": "green",
    }

    request.site = Site.objects.get(name=SiteName.EXPORTER)
    assert header_colour(request) == {
        "CHANGE_HEADER_COLOUR": True,
        "HEADER_COLOUR": "grey",
    }

    request.site = Site.objects.get(name=SiteName.CASEWORKER)
    assert header_colour(request) == {
        "CHANGE_HEADER_COLOUR": True,
        "HEADER_COLOUR": "red",
    }


@override_settings(
    APP_ENV="production",
)
def test_environment_information_show_environment_banner(rf: RequestFactory, db):
    request = rf.request()
    request.site = Site.objects.get(name=SiteName.IMPORTER)

    assert header_colour(request) == {
        "CHANGE_HEADER_COLOUR": False,
        "HEADER_COLOUR": "green",
    }
