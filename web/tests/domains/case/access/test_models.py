import pytest

from web.models import ExporterAccessRequest, ImporterAccessRequest, Process


@pytest.mark.parametrize(
    "kls",
    [ImporterAccessRequest, ExporterAccessRequest],
)
@pytest.mark.django_db
def test_access_request_downcast(kls, test_access_user):
    obj = kls.objects.create(
        submitted_by=test_access_user,
        process_type=kls.PROCESS_TYPE,
    )

    # if we already have the specific model, downcast should be a no-op
    assert id(obj) == id(obj.get_specific_model())

    # if we don't, it should load the correct type from the db, and it should be a new instance
    p = Process.objects.get(pk=obj.pk)

    downcast = p.get_specific_model()
    assert type(downcast) is kls
    assert id(obj) != id(downcast)
