from django.test import TestCase

from web.domains.mailshot.forms import (MailshotFilter, MailshotForm,
                                        MailshotRetractForm,
                                        ReceivedMailshotsFilter)
from web.domains.mailshot.models import Mailshot
from web.tests.domains.exporter.factory import ExporterFactory
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.user.factory import UserFactory

from .factory import MailshotFactory


class MailshotsFilterTest(TestCase):
    def setUp(self):
        MailshotFactory(title='Draft Mailshot',
                        description='This is a draft mailshot',
                        status=Mailshot.DRAFT,
                        is_active=False)
        MailshotFactory(title='Published Mailshot',
                        description='This is a published mailshot',
                        status=Mailshot.PUBLISHED,
                        is_active=True)
        MailshotFactory(title='Retracted Mailshot',
                        description='This is a retracted mailshot',
                        status=Mailshot.RETRACTED,
                        is_active=True)
        MailshotFactory(title='Cancelled Mailshot',
                        description='This is a cancelled mailshot',
                        status=Mailshot.CANCELLED,
                        is_active=True)

    def run_filter(self, data=None):
        return MailshotFilter(data=data).qs

    def test_title_filter(self):
        results = self.run_filter({'title': 'Mailshot'})
        self.assertEqual(results.count(), 4)

    def test_description_filter(self):
        results = self.run_filter({'description': 'published'})
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().title, 'Published Mailshot')

    def test_status_filter(self):
        results = self.run_filter({'status': Mailshot.RETRACTED})
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().title, 'Retracted Mailshot')

    def test_filter_order(self):
        results = self.run_filter({'title': 'mailshot'})
        self.assertEqual(results.count(), 4)
        first = results.first()
        last = results.last()
        self.assertEqual(first.title, 'Cancelled Mailshot')
        self.assertEqual(last.title, 'Draft Mailshot')


class ReceivedMailshotsFilterTest(TestCase):
    def create_mailshots(self):
        MailshotFactory(title='Draft Mailshot',
                        description='This is a draft mailshot',
                        status=Mailshot.DRAFT)
        MailshotFactory(title='Retracted Mailshot',
                        description='This is a retracted mailshot',
                        status=Mailshot.RETRACTED,
                        is_to_importers=True,
                        is_to_exporters=True)
        MailshotFactory(title='Cancelled Mailshot',
                        description='This is a cancelled mailshot',
                        status=Mailshot.CANCELLED,
                        is_to_importers=True,
                        is_to_exporters=True)
        MailshotFactory(
            title='Published Mailshot to importers',
            description='This is a published mailshot to importers',
            status=Mailshot.PUBLISHED,
            is_to_importers=True,
            is_to_exporters=False)
        MailshotFactory(
            title='Published Mailshot to exporters',
            description='This is a published mailshot to exporters',
            status=Mailshot.PUBLISHED,
            is_to_importers=False,
            is_to_exporters=True)
        MailshotFactory(title='Published Mailshot to all',
                        description='This is a published mailshot to all',
                        status=Mailshot.PUBLISHED,
                        is_to_importers=True,
                        is_to_exporters=True)

    def setUp(self):
        self.user = UserFactory(is_superuser=False)
        self.superuser = UserFactory(is_superuser=True)
        self.importer_organisation = ImporterFactory(is_active=True)
        self.individual_importer = ImporterFactory(is_active=True)
        self.exporter = ExporterFactory(is_active=True)
        self.create_mailshots()

    def run_filter(self, data=None, user=None):
        return ReceivedMailshotsFilter(data=data, user=user).qs

    def test_filter_only_gets_published_mailshots(self):
        self.individual_importer.user = self.user
        self.individual_importer.save()
        self.exporter.members.add(self.user)
        results = self.run_filter({'title': 'Mailshot'}, user=self.user)
        self.assertEqual(results.count(), 3)
        self.assertTrue(results[0].status, Mailshot.PUBLISHED)
        self.assertTrue(results[1].status, Mailshot.PUBLISHED)
        self.assertTrue(results[2].status, Mailshot.PUBLISHED)

    def test_superuser_gets_all_published_mailshots(self):
        results = self.run_filter({'title': 'Mailshot'}, user=self.superuser)
        self.assertEqual(results.count(), 3)
        self.assertTrue(results[0].status, Mailshot.PUBLISHED)
        self.assertTrue(results[1].status, Mailshot.PUBLISHED)
        self.assertTrue(results[2].status, Mailshot.PUBLISHED)

    def test_filter_only_gets_importer_mailshots(self):
        self.importer_organisation.members.add(self.user)
        results = self.run_filter({'title': 'Mailshot'}, user=self.user)
        self.assertEqual(results.count(), 2)
        self.assertEqual(results[0].title, 'Published Mailshot to all')
        self.assertEqual(results[1].title, 'Published Mailshot to importers')

    def test_filter_only_gets_exporter_mailshots(self):
        self.exporter.members.add(self.user)
        results = self.run_filter({'title': 'Mailshot'}, user=self.user)
        self.assertEqual(results.count(), 2)
        self.assertEqual(results[0].title, 'Published Mailshot to all')
        self.assertEqual(results[1].title, 'Published Mailshot to exporters')

    def test_title_filter(self):
        self.importer_organisation.members.add(self.user)
        self.exporter.members.add(self.user)
        results = self.run_filter({'title': 'mailshot'}, user=self.user)
        self.assertEqual(results.count(), 3)
        self.assertEqual(results[0].title, 'Published Mailshot to all')
        self.assertEqual(results[1].title, 'Published Mailshot to exporters')
        self.assertEqual(results[2].title, 'Published Mailshot to importers')

    def test_description_filter(self):
        self.importer_organisation.members.add(self.user)
        self.exporter.members.add(self.user)
        results = self.run_filter({'description': 'mailshot'}, user=self.user)
        self.assertEqual(results.count(), 3)
        self.assertEqual(results[0].description,
                         'This is a published mailshot to all')
        self.assertEqual(results[1].description,
                         'This is a published mailshot to exporters')
        self.assertEqual(results[2].description,
                         'This is a published mailshot to importers')


class MailshotFormTest(TestCase):
    def test_form_valid(self):
        form = MailshotForm(
            data={
                'title': 'Testing',
                'description': 'Description',
                'is_email': 'on',
                'email_subject': 'New Mailshot',
                'email_body': 'Email body',
                'recipients': ['importers']
            })
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = MailshotForm(data={
            'title': 'Test',
            'description': 'Description'
        })
        self.assertFalse(form.is_valid())

    def test_invalid_form_message(self):
        form = MailshotForm(
            data={
                'title': 'Test Mailshot',
                'description': 'Description',
                'is_email': False,
                'email_subject': 'New Mailshot',
                'email_body': 'Email body'
            })
        self.assertEqual(len(form.errors), 1)
        message = form.errors['recipients'][0]
        self.assertEqual(message, 'You must enter this item')


class MailshotRetractFormTest(TestCase):
    def test_form_valid(self):
        form = MailshotRetractForm(
            data={
                'is_retraction_email': 'on',
                'retract_email_subject': 'Retracted Mailshot',
                'retract_email_body': 'Email body'
            })
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = MailshotRetractForm(
            data={
                'is_retraction_email': 'Test',
                'retract_email_subject': 'Retracted Mailshot'
            })
        self.assertFalse(form.is_valid())

    def test_invalid_form_message(self):
        form = MailshotRetractForm(
            data={
                'is_retraction_email': 'Test',
                'retract_email_subject': 'Retracted Mailshot'
            })
        self.assertEqual(len(form.errors), 1)
        message = form.errors['retract_email_body'][0]
        self.assertEqual(message, 'You must enter this item')
