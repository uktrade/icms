import pytest

from web.models import Section5Clause
from web.views.actions import Unarchive


@pytest.mark.django_db
def test_list_ok(ilb_admin_user, ilb_admin_client):
    clause = Section5Clause.objects.first()
    clause.clause = "test-clause-value"
    clause.save()

    response = ilb_admin_client.get("/section5/", {"description": ""})

    assert response.status_code == 200
    assert "test-clause-value" in response.content.decode()


@pytest.mark.django_db
def test_create_ok(ilb_admin_client):
    Section5Clause.objects.count() == 1

    response = ilb_admin_client.get("/section5/create/")
    assert response.status_code == 200

    data = {"clause": "42bbb", "description": "Description for clause 42bbb"}
    response = ilb_admin_client.post("/section5/create/", data=data)
    assert response.status_code == 302

    Section5Clause.objects.count() == 2


@pytest.mark.django_db
def test_edit_ok(ilb_admin_user, ilb_admin_client):
    clause = Section5Clause.objects.first()

    response = ilb_admin_client.get(f"/section5/edit/{clause.pk}/")
    assert response.status_code == 200

    data = {"clause": "42bbb", "description": "Description for clause 42bbb"}
    response = ilb_admin_client.post(f"/section5/edit/{clause.pk}/", data=data)
    assert response.status_code == 302
    clause = Section5Clause.objects.get()
    assert response["Location"] == f"/section5/edit/{clause.pk}/"


@pytest.mark.django_db
def test_archived_not_editable(ilb_admin_user, ilb_admin_client):
    """Making sure that the only visible action for archived section5 clauses is the unarchive action"""
    new_section5 = Section5Clause.objects.first()
    new_section5.is_active = False
    new_section5.save()

    # confusing URL query param considering, but this fetches all archived section5 clauses
    response = ilb_admin_client.get("/section5/", {"is_active": "true"})

    for action in response.context_data["display"].actions:
        if action.display(new_section5) is True:
            assert isinstance(action, Unarchive)
