from django.test import TestCase

from web.domains.constabulary.forms import ConstabulariesFilter, ConstabularyForm
from web.models import Constabulary

from .factory import ConstabularyFactory


class TestConstabulariesFilter(TestCase):
    def setUp(self):
        # These tests pre-date the data migration that adds constabularies
        # therefore delete all real constabulary records before running these tests
        Constabulary.objects.all().delete()

        ConstabularyFactory(
            name="Test Constabulary",
            region=Constabulary.EAST_MIDLANDS,
            email="test_constabulary@example.com",  # /PS-IGNORE
            is_active=False,
        )
        ConstabularyFactory(
            name="Big London Constabulary",
            region=Constabulary.EASTERN,
            email="london_constabulary@example.com",  # /PS-IGNORE
            is_active=True,
        )
        ConstabularyFactory(
            name="That Constabulary",
            region=Constabulary.EASTERN,
            email="that_constabulary@example.com",  # /PS-IGNORE
            is_active=True,
        )

    def run_filter(self, data=None):
        return ConstabulariesFilter(data=data).qs

    def test_name_filter(self):
        results = self.run_filter({"name": "constab"})
        assert results.count() == 2

    def test_archived_filter(self):
        results = self.run_filter({"archived": True})
        assert results.count() == 1
        assert results.first().name == "Test Constabulary"

    def test_region_filter(self):
        results = self.run_filter({"region": Constabulary.EASTERN})
        assert results.count() == 2

    def test_email_filter(self):
        results = self.run_filter({"email": "@example.com"})
        assert results.count() == 2

    def test_filter_order(self):
        results = self.run_filter({"email": "example"})
        assert results.count() == 2
        first = results.first()
        last = results.last()
        assert first.name == "Big London Constabulary"
        assert last.name == "That Constabulary"


class TestConstabularyForm(TestCase):
    def test_form_valid(self):
        form = ConstabularyForm(
            data={
                "name": "Testing",
                "region": Constabulary.WEST_MIDLANDS,
                "email": "test@example.com",  # /PS-IGNORE
            }
        )
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = ConstabularyForm(
            data={"name": "Test", "region": Constabulary.ISLE_OF_MAN, "email": "invalidmail"}
        )
        assert form.is_valid() is False

    def test_invalid_form_message(self):
        form = ConstabularyForm(
            data={"name": "Test", "region": Constabulary.ISLE_OF_MAN, "email": "invalidmail"}
        )
        assert len(form.errors) == 1
        message = form.errors["email"][0]
        assert message == "Enter a valid email address."
