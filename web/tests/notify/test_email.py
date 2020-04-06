#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.core import mail
from django.test import TestCase

from web.domains.exporter.models import Exporter
from web.domains.importer.models import Importer
from web.domains.user.models import User, PersonalEmail, AlternativeEmail
from web.notify import email
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.user.factory import UserFactory


class TestEmail(TestCase):
    def create_user(self, account_status, emails=[]):
        user = UserFactory(account_status=account_status)
        for email in emails:
            email.user = user
            email.save()
        return user

    def create_importer_org(self, active=True, members=[]):
        importer = ImporterFactory(is_active=active,
                                   type=Importer.ORGANISATION)
        for member in members:
            if member.active:
                self.create_user()

        return importer

    def setUp(self):
        # An active import organisation
        self.active_importer_org = self.create_importer_org(members=[
            {
                'active':
                True,
                'personal': [{
                    'email': 'org_user@example.com',
                    'notify': True
                }, {
                    'email': 'org_user_no_notify@example.com',
                    'notify': False
                }],
                'alternative': [{
                    'email': 'org_user_alt@example.com',
                    'notify': True
                }, {
                    'email': 'org_user_alt_no_notify@example.com',
                    'notify': False
                }]
            },
        ])

        # An archived import organisation
        self.archived_importer_org = self.create_importer_org(
            active=False,
            members=[
                {
                    'active':
                    True,
                    'personal': [{
                        'email': 'archived_org_user@example.com',
                        'notify': True
                    }],
                    'alternative': [{
                        'email': 'archived_org_user_alt@example.com',
                        'notify': True
                    }]
                },
            ])
