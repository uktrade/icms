from django.test import TestCase

from web.domains.user.forms import UserFilter
from .factory import UserFactory


def run_filter(data=None):
    return UserFilter(data=data).qs


class UserFilterTest(TestCase):
    def setUp(self):
        UserFactory()

    def test_filter_results_count(self):
        results = run_filter()
        self.assertEqual(2, results.count())
