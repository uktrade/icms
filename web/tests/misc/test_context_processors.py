from django.test import RequestFactory, override_settings

from web.misc.context_processors import environment_information


@override_settings(
    CURRENT_BRANCH="test-branch", CURRENT_ENVIRONMENT="test", CURRENT_TAG="v1.0.0", DEBUG=True
)
def test_environment_information(rf: RequestFactory):
    assert environment_information(rf.request()) == {
        "CURRENT_ENVIRONMENT": "test",
        "CURRENT_BRANCH": "test-branch",
        "CURRENT_TAG": "v1.0.0",
        "SHOW_ENVIRONMENT_INFO": True,
    }


@override_settings(
    CURRENT_BRANCH="test-branch", CURRENT_ENVIRONMENT="test", CURRENT_TAG="v1.0.0", DEBUG=False
)
def test_environment_information_show_environment_banner(rf: RequestFactory):
    assert environment_information(rf.request()) == {
        "CURRENT_ENVIRONMENT": "test",
        "CURRENT_BRANCH": "test-branch",
        "CURRENT_TAG": "v1.0.0",
        "SHOW_ENVIRONMENT_INFO": False,
    }
