import pytest
from django.test import Client

from web.domains.section5.models import Section5Clause
from web.domains.user.models import User
from web.tests.domains.section5.factories import Section5ClauseFactory
from web.tests.domains.user.factory import UserFactory


@pytest.mark.django_db
def test_list_ok():
    ilb_admin = UserFactory.create(
        is_active=True,
        account_status=User.ACTIVE,
        password_disposition=User.FULL,
        permission_codenames=["ilb_admin"],
    )
    Section5ClauseFactory.create(clause="42aaa", created_by=ilb_admin)

    client = Client()
    client.login(username=ilb_admin.username, password="test")
    response = client.get("/section5/")

    assert response.status_code == 200
    assert "42aaa" in response.content.decode()


@pytest.mark.django_db
def test_create_ok():
    ilb_admin = UserFactory.create(
        is_active=True,
        account_status=User.ACTIVE,
        password_disposition=User.FULL,
        permission_codenames=["ilb_admin"],
    )

    client = Client()
    client.login(username=ilb_admin.username, password="test")
    response = client.get("/section5/create/")
    assert response.status_code == 200

    data = {"clause": "42bbb", "description": "Description for clause 42bbb"}
    response = client.post("/section5/create/", data=data)
    assert response.status_code == 302
    clause = Section5Clause.objects.get()
    assert response["Location"] == f"/section5/edit/{clause.pk}/"


@pytest.mark.django_db
def test_edit_ok():
    ilb_admin = UserFactory.create(
        is_active=True,
        account_status=User.ACTIVE,
        password_disposition=User.FULL,
        permission_codenames=["ilb_admin"],
    )
    clause = Section5ClauseFactory.create(created_by=ilb_admin)

    client = Client()
    client.login(username=ilb_admin.username, password="test")
    response = client.get(f"/section5/edit/{clause.pk}/")
    assert response.status_code == 200

    data = {"clause": "42bbb", "description": "Description for clause 42bbb"}
    response = client.post(f"/section5/edit/{clause.pk}/", data=data)
    assert response.status_code == 302
    clause = Section5Clause.objects.get()
    assert response["Location"] == f"/section5/edit/{clause.pk}/"
