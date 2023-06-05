import pytest

from web.models import ExporterAccessRequest, ImporterAccessRequest, Process


@pytest.mark.parametrize(
    "kls",
    [ImporterAccessRequest, ExporterAccessRequest],
)
@pytest.mark.django_db
def test_access_request_downcast(kls, access_request_user):
    obj = kls.objects.create(
        submitted_by=access_request_user,
        process_type=kls.PROCESS_TYPE,
    )

    # if we already have the specific model, downcast should be a no-op
    assert id(obj) == id(obj.get_specific_model())

    # if we don't, it should load the correct type from the db, and it should be a new instance
    p = Process.objects.get(pk=obj.pk)

    downcast = p.get_specific_model()
    assert type(downcast) is kls
    assert id(obj) != id(downcast)


@pytest.mark.parametrize(
    ["access_request", "is_agent_request"],
    [
        (ImporterAccessRequest(request_type="MAIN_IMPORTER_ACCESS"), False),
        (ImporterAccessRequest(request_type="AGENT_IMPORTER_ACCESS"), True),
        (ExporterAccessRequest(request_type="MAIN_EXPORTER_ACCESS"), False),
        (ExporterAccessRequest(request_type="AGENT_EXPORTER_ACCESS"), True),
    ],
)
def test_is_agent_request(
    access_request: ImporterAccessRequest | ExporterAccessRequest, is_agent_request: bool
) -> None:
    assert access_request.is_agent_request is is_agent_request
