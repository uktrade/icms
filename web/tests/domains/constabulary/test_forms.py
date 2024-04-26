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
            telephone_number="02071234567",  # /PS-IGNORE
        )
        ConstabularyFactory(
            name="Big London Constabulary",
            region=Constabulary.EASTERN,
            email="london_constabulary@example.com",  # /PS-IGNORE
            is_active=True,
            telephone_number="02071235217",  # /PS-IGNORE
        )
        ConstabularyFactory(
            name="That Constabulary",
            region=Constabulary.EASTERN,
            email="that_constabulary@example.com",  # /PS-IGNORE
            is_active=True,
            telephone_number="02071234127",  # /PS-IGNORE
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

    def test_telephone_number_filter(self):
        results = self.run_filter({"telephone_number": "02071234127"})
        assert results.count() == 1

    def test_filter_order(self):
        results = self.run_filter({"email": "example"})
        assert results.count() == 2
        first = results.first()
        last = results.last()
        assert first.name == "Big London Constabulary"
        assert last.name == "That Constabulary"

    def test_form_name_field(self):
        """Tests that the form field is a ModelChoiceField with the correct ICMSModelSelect2Widget."""
        form = ConstabulariesFilter().form
        assert form.fields["name"].widget.__class__.__name__ == "ICMSModelSelect2Widget"
        assert form.fields["name"].queryset.model == Constabulary
        assert form.fields["name"].widget.search_fields == ("name__icontains",)


class TestConstabularyForm(TestCase):
    def test_form_valid(self):
        form = ConstabularyForm(
            data={
                "name": "Testing",
                "region": Constabulary.WEST_MIDLANDS,
                "email": "test@example.com",  # /PS-IGNORE
                "telephone_number": "02071234567",  # /PS-IGNORE
            }
        )
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = ConstabularyForm(
            data={
                "name": "Test",
                "region": Constabulary.ISLE_OF_MAN,
                "email": "invalidmail",
                "telephone_number": "02071234567",
            }
        )
        assert form.is_valid() is False

    def test_invalid_form_message(self):
        form = ConstabularyForm(
            data={
                "name": "Test",
                "region": Constabulary.ISLE_OF_MAN,
                "email": "invalidmail",
                "telephone_number": "02071234567",
            }
        )
        assert len(form.errors) == 1
        message = form.errors["email"][0]
        assert message == "Enter a valid email address."

    def test_form_telephone_number_invalid_letters(self):
        form = ConstabularyForm(
            data={
                "name": "Test",
                "region": Constabulary.ISLE_OF_MAN,
                "email": "test@example.com",  # /PS-IGNORE
                "telephone_number": "02071234567a",
            }
        )
        assert len(form.errors) == 1
        message = form.errors["telephone_number"][0]
        assert message == "Telephone number must contain only digits."

    def test_form_telephone_number_invalid_leading_zero(self):
        form = ConstabularyForm(
            data={
                "name": "Test",
                "region": Constabulary.ISLE_OF_MAN,
                "email": "test@example.com",  # /PS-IGNORE
                "telephone_number": "20712345678",
            }
        )
        assert len(form.errors) == 1
        message = form.errors["telephone_number"][0]
        assert message == "Telephone number must start with 0."

    def test_form_telephone_number_invalid_too_short(self):
        form = ConstabularyForm(
            data={
                "name": "Test",
                "region": Constabulary.ISLE_OF_MAN,
                "email": "test@example.com",  # /PS-IGNORE
                "telephone_number": "0203",
            }
        )
        assert len(form.errors) == 1
        message = form.errors["telephone_number"][0]
        assert message == "Telephone number must contain at least 10 digits."

    def test_form_telephone_number_stripped_of_whitespace(self):
        form = ConstabularyForm(
            data={
                "name": "Testing",
                "region": Constabulary.WEST_MIDLANDS,
                "email": "test@example.com",  # /PS-IGNORE
                "telephone_number": "0207 1234 567",  # /PS-IGNORE
            }
        )
        assert form.is_valid() is True
        assert form.cleaned_data["telephone_number"] == "02071234567"
