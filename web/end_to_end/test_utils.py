from . import utils


def test_get_application_id() -> None:
    url = "http://caseworker:8008/import/firearms/dfl/1234/edit/"
    pattern = r"import/firearms/dfl/(?P<app_pk>\d+)/edit/"

    app_pk = utils.get_application_id(url, pattern)

    assert app_pk == 1234
