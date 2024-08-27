from unittest.mock import Mock

import pytest
from django.contrib.auth.models import Group
from django.test import TestCase

from web.domains.case.services import reference
from web.domains.mailshot.forms import (
    MailshotFilter,
    MailshotForm,
    MailshotRetractForm,
    ReceivedMailshotsFilter,
)
from web.models import Mailshot
from web.permissions import Perms
from web.tests.auth import AuthTestCase


class TestMailshotsFilter(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, db):
        Mailshot.objects.create(
            title="Draft Mailshot",
            description="This is a draft mailshot",
            status=Mailshot.Statuses.DRAFT,
            is_active=False,
            created_by=self.importer_two_user,
        )
        Mailshot.objects.create(
            title="Published Mailshot",
            description="This is a published mailshot",
            status=Mailshot.Statuses.PUBLISHED,
            is_active=True,
            created_by=self.importer_two_user,
        )
        Mailshot.objects.create(
            title="Retracted Mailshot",
            description="This is a retracted mailshot",
            status=Mailshot.Statuses.RETRACTED,
            is_active=True,
            created_by=self.importer_two_user,
        )
        Mailshot.objects.create(
            title="Cancelled Mailshot",
            description="This is a cancelled mailshot",
            status=Mailshot.Statuses.CANCELLED,
            is_active=True,
            created_by=self.importer_two_user,
        )

    def run_filter(self, data=None):
        return MailshotFilter(data=data).qs

    def test_title_filter(self):
        results = self.run_filter({"title": "Mailshot"})
        assert results.count() == 4

    def test_description_filter(self):
        results = self.run_filter({"description": "published"})
        assert results.count() == 1
        assert results.first().title == "Published Mailshot"

    def test_status_filter(self):
        results = self.run_filter({"status": Mailshot.Statuses.RETRACTED})
        assert results.count() == 1
        assert results.first().title == "Retracted Mailshot"

    def test_filter_order(self):
        results = self.run_filter({"title": "mailshot"})
        assert results.count() == 4
        first = results.first()
        last = results.last()
        assert first.title == "Cancelled Mailshot"
        assert last.title == "Draft Mailshot"


class TestReceivedMailshotsFilter:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        importer_one_contact,
        importer_two_contact,
        exporter_one_contact,
        ilb_admin_user,
    ):
        self.importer = importer_one_contact
        self.exporter = exporter_one_contact
        self.ilb_admin = ilb_admin_user

        # Use importer two main contact as a user with both Importer & Exporter permissions
        exporter_group = Group.objects.get(name=Perms.obj.exporter.get_group_name())
        importer_two_contact.groups.add(exporter_group)
        self.importer_exporter = importer_two_contact

        Mailshot.objects.create(
            title="Draft Mailshot",
            description="This is a draft mailshot",
            status=Mailshot.Statuses.DRAFT,
            created_by=importer_two_contact,
        )
        Mailshot.objects.create(
            title="Retracted Mailshot",
            description="This is a retracted mailshot",
            status=Mailshot.Statuses.RETRACTED,
            is_to_importers=True,
            is_to_exporters=True,
            created_by=importer_two_contact,
        )
        Mailshot.objects.create(
            title="Cancelled Mailshot",
            description="This is a cancelled mailshot",
            status=Mailshot.Statuses.CANCELLED,
            is_to_importers=True,
            is_to_exporters=True,
            created_by=importer_two_contact,
        )
        Mailshot.objects.create(
            title="Published Mailshot to importers",
            description="This is a published mailshot to importers",
            status=Mailshot.Statuses.PUBLISHED,
            is_to_importers=True,
            is_to_exporters=False,
            created_by=importer_two_contact,
        )
        Mailshot.objects.create(
            title="Published Mailshot to exporters",
            description="This is a published mailshot to exporters",
            status=Mailshot.Statuses.PUBLISHED,
            is_to_importers=False,
            is_to_exporters=True,
            created_by=importer_two_contact,
        )
        Mailshot.objects.create(
            title="Published Mailshot to all",
            description="This is a published mailshot to all",
            status=Mailshot.Statuses.PUBLISHED,
            is_to_importers=True,
            is_to_exporters=True,
            created_by=importer_two_contact,
        )

    def run_filter(self, data=None, user=None):
        return ReceivedMailshotsFilter(data=data, user=user).qs

    def test_filter_only_gets_published_mailshots(self):
        results = self.run_filter({"title": "Mailshot"}, user=self.importer_exporter)
        assert results.count() == 3
        assert results[0].status == Mailshot.Statuses.PUBLISHED
        assert results[1].status == Mailshot.Statuses.PUBLISHED
        assert results[2].status == Mailshot.Statuses.PUBLISHED

    def test_case_worker_gets_all_published_mailshots(self):
        results = self.run_filter({"title": "Mailshot"}, user=self.ilb_admin)
        assert results.count() == 3
        assert results[0].status == Mailshot.Statuses.PUBLISHED
        assert results[1].status == Mailshot.Statuses.PUBLISHED
        assert results[2].status == Mailshot.Statuses.PUBLISHED

    def test_filter_only_gets_importer_mailshots(self):
        results = self.run_filter({"title": "Mailshot"}, user=self.importer)
        assert results.count() == 2
        assert results[0].title == "Published Mailshot to all"
        assert results[1].title == "Published Mailshot to importers"

    def test_filter_only_gets_exporter_mailshots(self):
        results = self.run_filter({"title": "Mailshot"}, user=self.exporter)
        assert results.count() == 2
        assert results[0].title == "Published Mailshot to all"
        assert results[1].title == "Published Mailshot to exporters"

    def test_title_filter(self):
        results = self.run_filter({"title": "mailshot"}, user=self.importer_exporter)
        assert results.count() == 3
        assert results[0].title == "Published Mailshot to all"
        assert results[1].title == "Published Mailshot to exporters"
        assert results[2].title == "Published Mailshot to importers"

    def test_description_filter(self):
        results = self.run_filter({"description": "mailshot"}, user=self.importer_exporter)
        assert results.count() == 3
        assert results[0].description == "This is a published mailshot to all"
        assert results[1].description == "This is a published mailshot to exporters"
        assert results[2].description == "This is a published mailshot to importers"

    def test_id_reference_filter(self):
        # first checking if searching by reference (e.g. MAIL/1) works
        mailshot_object = Mailshot.objects.filter(status=Mailshot.Statuses.PUBLISHED).first()
        mailshot_object.reference = reference.get_mailshot_reference(lock_manager=Mock())
        mailshot_object.save()

        results = self.run_filter(
            {"id_reference": mailshot_object.reference}, user=self.importer_exporter
        )
        assert results.count() == 1
        assert results.get() == mailshot_object

        # now let's check if searching by the ID works
        results = self.run_filter({"id_reference": mailshot_object.pk}, user=self.importer_exporter)
        assert results.count() == 1
        assert results.get() == mailshot_object


class TestMailshotForm(TestCase):
    def test_form_valid(self):
        form = MailshotForm(
            data={
                "title": "Testing",
                "description": "Description",
                "is_email": "on",
                "email_subject": "New Mailshot",
                "email_body": "Email body",
                "recipients": ["importers"],
            }
        )
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = MailshotForm(data={"title": "Test", "description": "Description"})
        assert form.is_valid() is False

    def test_invalid_form_message(self):
        form = MailshotForm(
            data={
                "title": "Test Mailshot",
                "description": "Description",
                "is_email": False,
                "email_subject": "New Mailshot",
                "email_body": "Email body",
            }
        )
        assert len(form.errors) == 1
        message = form.errors["recipients"][0]
        assert message == "You must enter this item"


class TestMailshotRetractForm(TestCase):
    def test_form_valid(self):
        form = MailshotRetractForm(
            data={
                "is_retraction_email": "on",
                "retract_email_subject": "Retracted Mailshot",
                "retract_email_body": "Email body",
            }
        )
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = MailshotRetractForm(
            data={"is_retraction_email": "Test", "retract_email_subject": "Retracted Mailshot"}
        )
        assert form.is_valid() is False

    def test_invalid_form_message(self):
        form = MailshotRetractForm(
            data={"is_retraction_email": "Test", "retract_email_subject": "Retracted Mailshot"}
        )
        assert len(form.errors) == 1
        message = form.errors["retract_email_body"][0]
        assert message == "You must enter this item"
