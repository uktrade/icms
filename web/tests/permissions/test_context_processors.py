import pytest
from django.http.request import HttpRequest
from guardian.utils import get_anonymous_user

from web.permissions.context_processors import (
    UserObjectPerms,
    request_user_object_permissions,
)


class TestUserObjectPerms:
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        importer,
        exporter,
        importer_one_main_contact,
        exporter_one_main_contact,
        fa_sil_app,
        com_app,
    ):
        self.importer = importer
        self.exporter = exporter
        self.importer_contact = importer_one_main_contact
        self.exporter_contact = exporter_one_main_contact

        self.fa_sil_app = fa_sil_app
        self.com_app = com_app

    def test_permissions(self):
        importer_uop = UserObjectPerms(self.importer_contact)
        exporter_uop = UserObjectPerms(self.exporter_contact)

        assert importer_uop.can_edit_org(self.importer)
        assert importer_uop.can_manage_org_contacts(self.importer)
        assert importer_uop.can_user_view_org(self.importer)
        assert importer_uop.can_view_application(self.fa_sil_app)
        assert not exporter_uop.can_edit_org(self.importer)
        assert not exporter_uop.can_manage_org_contacts(self.importer)
        assert not exporter_uop.can_user_view_org(self.importer)
        assert not exporter_uop.can_view_application(self.fa_sil_app)

        assert exporter_uop.can_edit_org(self.exporter)
        assert exporter_uop.can_manage_org_contacts(self.exporter)
        assert exporter_uop.can_user_view_org(self.exporter)
        assert exporter_uop.can_view_application(self.com_app)
        assert not importer_uop.can_edit_org(self.exporter)
        assert not importer_uop.can_manage_org_contacts(self.exporter)
        assert not importer_uop.can_user_view_org(self.exporter)
        assert not importer_uop.can_view_application(self.com_app)


def test_request_user_object_permissions(importer_one_main_contact):
    anon_user = get_anonymous_user()

    user_request = HttpRequest()
    context = request_user_object_permissions(user_request)
    uop = context["user_obj_perms"]

    assert uop.user == anon_user

    user_request.user = importer_one_main_contact
    context = request_user_object_permissions(user_request)
    uop = context["user_obj_perms"]

    assert uop.user == importer_one_main_contact
