import pytest

from web.models import Section5Clause
from web.tests.domains.section5.factories import Section5ClauseFactory


@pytest.mark.django_db
def test_list_ok(ilb_admin_user, ilb_admin_client):
    Section5ClauseFactory.create(clause="42aaa", created_by=ilb_admin_user)

    response = ilb_admin_client.get("/section5/", {"description": ""})

    assert response.status_code == 200
    assert "42aaa" in response.content.decode()


@pytest.mark.django_db
def test_create_ok(ilb_admin_client):
    response = ilb_admin_client.get("/section5/create/")
    assert response.status_code == 200

    data = {"clause": "42bbb", "description": "Description for clause 42bbb"}
    response = ilb_admin_client.post("/section5/create/", data=data)
    assert response.status_code == 302
    clause = Section5Clause.objects.get()
    assert response["Location"] == f"/section5/edit/{clause.pk}/"


@pytest.mark.django_db
def test_edit_ok(ilb_admin_user, ilb_admin_client):
    clause = Section5ClauseFactory.create(created_by=ilb_admin_user)

    response = ilb_admin_client.get(f"/section5/edit/{clause.pk}/")
    assert response.status_code == 200

    data = {"clause": "42bbb", "description": "Description for clause 42bbb"}
    response = ilb_admin_client.post(f"/section5/edit/{clause.pk}/", data=data)
    assert response.status_code == 302
    clause = Section5Clause.objects.get()
    assert response["Location"] == f"/section5/edit/{clause.pk}/"
