#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.core import mail
from django.test import TestCase

from web.domains.importer.models import Importer
from web.domains.user.models import AlternativeEmail, PersonalEmail, User
from web.notify import email
from web.tests.domains.exporter.factory import ExporterFactory
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.user.factory import UserFactory


class TestEmail(TestCase):
    def create_user(self, account_status, emails=[]):
        user = UserFactory(account_status=account_status)
        return user

    def create_importer_org(self, name=None, active=True, members=[]):
        importer = ImporterFactory(is_active=active, name=name, type=Importer.ORGANISATION)
        for member in members:
            if member["active"]:
                user = self.create_user(account_status=User.ACTIVE)
            else:
                user = self.create_user(account_status=User.CANCELLED)

            for m in member["personal"]:
                PersonalEmail(user=user, email=m["email"], portal_notifications=m["notify"]).save()
            if "alternative" in member:
                for m in member["alternative"]:
                    AlternativeEmail(
                        user=user, email=m["email"], portal_notifications=m["notify"]
                    ).save()

            importer.members.add(user)

    def create_individual_importer(self, name=None, active=True, user=None):
        is_active = user["active"]
        if is_active:
            _user = self.create_user(account_status=User.ACTIVE)
        else:
            _user = self.create_user(account_status=User.BLOCKED)

        ImporterFactory(is_active=active, user=_user, name=name, type=Importer.INDIVIDUAL)
        for m in user["personal"]:
            PersonalEmail(user=_user, email=m["email"], portal_notifications=m["notify"]).save()

    def create_exporter(self, name=None, active=True, members=[]):
        exporter = ExporterFactory(is_active=active, name=name)
        for member in members:
            if member["active"]:
                user = self.create_user(account_status=User.ACTIVE)
            else:
                user = self.create_user(account_status=User.CANCELLED)

            for m in member["personal"]:
                PersonalEmail(user=user, email=m["email"], portal_notifications=m["notify"]).save()
            if "alternative" in member:
                for m in member["alternative"]:
                    AlternativeEmail(
                        user=user, email=m["email"], portal_notifications=m["notify"]
                    ).save()

            exporter.members.add(user)

    def setup_importers(self):
        # An active import organisation
        self.create_importer_org(
            name="An import organisation",
            members=[
                {
                    "active": True,
                    "personal": [
                        {"email": "active_org_user@example.com", "notify": True},
                        {"email": "active_org_user_second_email@example.com", "notify": True},
                        {"email": "active_org_user_no_notify@example.com", "notify": False},
                    ],
                    "alternative": [
                        {"email": "active_org_user_alt@example.com", "notify": True},
                        {"email": "active_org_user_alt_no_notify@example.com", "notify": False},
                    ],
                },
                {
                    "active": True,
                    "personal": [{"email": "second_active_org_user@example.com", "notify": True}],
                    "alternative": [
                        {"email": "second_active_org_user_alt@example.com", "notify": True}
                    ],
                },
                {
                    "active": False,
                    "personal": [{"email": "deactive_org_user@example.com", "notify": True}],
                },
            ],
        )

        # An archived import organisation
        self.create_importer_org(
            name="Another import organisation",
            active=False,
            members=[
                {
                    "active": True,
                    "personal": [{"email": "archived_org_user@example.com", "notify": True}],
                    "alternative": [{"email": "archived_org_user_alt@example.com", "notify": True}],
                },
            ],
        )

        # An active individual importer
        self.create_individual_importer(
            active=True,
            name="An individual importer",
            user={
                "active": True,
                "personal": [
                    {"email": "ind_importer_user@example.com", "notify": True},
                    {"email": "ind_importer_no_notify@example.com", "notify": False},
                ],
            },
        )

        # An archived individual importer
        self.create_individual_importer(
            active=False,
            name="Another individual importer",
            user={
                "active": True,
                "personal": [
                    {"email": "deactive_ind_importer_user@example.com", "notify": True},
                    {"email": "deactive_ind_importer_no_notify@example.com", "notify": False},
                ],
            },
        )

    def setup_exporters(self):
        # An active exporter
        self.create_exporter(
            name="An exporter",
            members=[
                {
                    "active": True,
                    "personal": [
                        {"email": "active_export_user@example.com", "notify": True},
                        {"email": "active_export_user_no_notify@example.com", "notify": False},
                    ],
                    "alternative": [
                        {"email": "active_export_user_alt@example.com", "notify": True},
                        {"email": "active_export_user_alt_no_notify@example.com", "notify": False},
                    ],
                },
                {
                    "active": True,
                    "personal": [
                        {"email": "second_active_export_user@example.com", "notify": True}
                    ],
                },
                {
                    "active": False,
                    "personal": [{"email": "deactive_export_user@example.com", "notify": True}],
                },
            ],
        )

        # An archived import organisation
        self.create_exporter(
            name="Another exporter",
            active=False,
            members=[
                {
                    "active": True,
                    "personal": [{"email": "archived_export_user@example.com", "notify": True}],
                    "alternative": [
                        {"email": "archived_export_user_alt@example.com", "notify": True}
                    ],
                },
            ],
        )

    def setUp(self):
        self.setup_importers()
        self.setup_exporters()

    def test_send_email(self):
        email.send_email.delay(
            "Test subject",
            "Test message",
            ["test@example.com", "test2@example.com"],
            html_message="<p>Test message</p>",
        )
        outbox = mail.outbox
        assert len(outbox) == 1
        assert "test@example.com" in outbox[0].to
        assert "test2@example.com" in outbox[0].to

    def test_send_mailshot_to_importers(self):
        email.send_mailshot.delay(
            "Test subject", "Test message", html_message="<p>Test message</p>", to_importers=True
        )
        outbox = mail.outbox
        assert len(outbox) == 3
        # Many-to-many relations order is not guaranteed
        # Members of exporter team might have different order
        # Testing by length
        for o in outbox:
            if len(o.to) == 3:
                assert "active_org_user@example.com" in o.to
                assert "active_org_user_second_email@example.com" in o.to
                assert "active_org_user_alt@example.com" in o.to
            elif len(o.to) == 2:
                assert "second_active_org_user@example.com" in o.to
                assert "second_active_org_user_alt@example.com" in o.to
            elif len(o.to) == 1:
                assert "ind_importer_user@example.com" in o.to
            else:
                raise AssertionError("Test failed with invalid email recipients")

    def test_send_mailshot_to_exporters(self):
        email.send_mailshot.delay(
            "Test subject", "Test message", html_message="<p>Test message</p>", to_exporters=True
        )
        outbox = mail.outbox
        assert len(outbox) == 2
        # Many-to-many relations order is not guaranteed
        # Members of exporter team might have different order
        # Testing by length
        for o in outbox:
            if len(o.to) == 2:
                assert "active_export_user@example.com" in o.to
                assert "active_export_user_alt@example.com" in o.to
            elif len(o.to) == 1:
                assert "second_active_export_user@example.com" in o.to
            else:
                raise AssertionError("Test failed with invalid email recipients")
