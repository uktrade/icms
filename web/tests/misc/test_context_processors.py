from django.contrib.sites.models import Site
from django.test import RequestFactory, override_settings

from web.misc.context_processors import environment_information
from web.sites import SiteName


@override_settings(
    CURRENT_BRANCH="test-branch", CURRENT_ENVIRONMENT="test", CURRENT_TAG="v1.0.0", DEBUG=True
)
def test_environment_information(rf: RequestFactory, db):
    request = rf.request()
    request.site = Site.objects.get(name=SiteName.IMPORTER)
    assert environment_information(request) == {
        "CURRENT_ENVIRONMENT": "test",
        "CURRENT_BRANCH": "test-branch",
        "CURRENT_TAG": "v1.0.0",
        "SHOW_ENVIRONMENT_INFO": True,
        "HEADER_COLOUR": "green",
    }

    request.site = Site.objects.get(name=SiteName.EXPORTER)
    assert environment_information(request) == {
        "CURRENT_ENVIRONMENT": "test",
        "CURRENT_BRANCH": "test-branch",
        "CURRENT_TAG": "v1.0.0",
        "SHOW_ENVIRONMENT_INFO": True,
        "HEADER_COLOUR": "grey",
    }

    request.site = Site.objects.get(name=SiteName.CASEWORKER)
    assert environment_information(request) == {
        "CURRENT_ENVIRONMENT": "test",
        "CURRENT_BRANCH": "test-branch",
        "CURRENT_TAG": "v1.0.0",
        "SHOW_ENVIRONMENT_INFO": True,
        "HEADER_COLOUR": "red",
    }


@override_settings(
    CURRENT_BRANCH="test-branch", CURRENT_ENVIRONMENT="test", CURRENT_TAG="v1.0.0", DEBUG=False
)
def test_environment_information_show_environment_banner(rf: RequestFactory, db):
    request = rf.request()
    request.site = Site.objects.get(name=SiteName.IMPORTER)

    assert environment_information(request) == {
        "CURRENT_ENVIRONMENT": "test",
        "CURRENT_BRANCH": "test-branch",
        "CURRENT_TAG": "v1.0.0",
        "SHOW_ENVIRONMENT_INFO": False,
        "HEADER_COLOUR": "green",
    }
