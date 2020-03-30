from django.test import TestCase

from web.domains.mailshot.forms import MailshotFilter
from web.domains.mailshot.models import Mailshot

from .factory import MailshotFactory


class ConstabulariesFilterTest(TestCase):
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
