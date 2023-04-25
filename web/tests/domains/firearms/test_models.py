from django.test import TestCase

from web.models import ObsoleteCalibre, ObsoleteCalibreGroup

from .factory import ObsoleteCalibreFactory, ObsoleteCalibreGroupFactory


class TestObsoleteCalibreGroup(TestCase):
    def test_create_calibre_group(self):
        calibre_group = ObsoleteCalibreGroupFactory(name="Test Group", order=1)
        assert isinstance(calibre_group, ObsoleteCalibreGroup)
        assert calibre_group.name == "Test Group"
        assert calibre_group.order == 1

    def test_archive_calibre_group(self):
        calibre_group = ObsoleteCalibreGroupFactory(is_active=True)
        calibre_group.archive()
        assert calibre_group.is_active is False

    def test_unarchive_calibre_group(self):
        calibre_group = ObsoleteCalibreGroupFactory(is_active=False)
        calibre_group.unarchive()
        assert calibre_group.is_active is True

    def test_string_representation(self):
        calibre_group = ObsoleteCalibreGroupFactory(name="Test")
        assert calibre_group.__str__() == "Obsolete Calibre Group (Test)"


class TestObsoleteCalibre(TestCase):
    def test_create_calibre(self):
        calibre = ObsoleteCalibreFactory(name="Test Calibre", order=1)
        assert isinstance(calibre, ObsoleteCalibre)
        assert calibre.name == "Test Calibre"
        assert calibre.order == 1

    def test_archive_calibre(self):
        calibre = ObsoleteCalibreFactory(is_active=True)
        calibre.archive()
        assert calibre.is_active is False

    def test_unarchive_calibre(self):
        calibre = ObsoleteCalibreFactory(is_active=False)
        calibre.unarchive()
        assert calibre.is_active is True

    def test_status(self):
        calibre = ObsoleteCalibre()
        calibre.name = "Test Calibre"
        calibre.order = 1
        calibre.calibre_group = ObsoleteCalibreGroupFactory()
        assert calibre.status == "Pending"
        calibre.save()
        assert calibre.status == "Current"
        calibre.archive()
        assert calibre.status == "Archived"

    def test_string_representation(self):
        calibre = ObsoleteCalibreFactory(name="Test")
        assert calibre.__str__() == "Obsolete Calibre (Test)"
