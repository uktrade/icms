from django.test import TestCase

from web.domains.firearms.models import ObsoleteCalibre, ObsoleteCalibreGroup

from .factory import ObsoleteCalibreFactory, ObsoleteCalibreGroupFactory


class ObsoleteCalibreGroupTest(TestCase):
    def test_create_calibre_group(self):
        calibre_group = ObsoleteCalibreGroupFactory(name="Test Group", order=1)
        self.assertTrue(isinstance(calibre_group, ObsoleteCalibreGroup))
        self.assertEqual(calibre_group.name, "Test Group")
        self.assertEqual(calibre_group.order, 1)

    def test_archive_calibre_group(self):
        calibre_group = ObsoleteCalibreGroupFactory(is_active=True)
        calibre_group.archive()
        self.assertFalse(calibre_group.is_active)

    def test_unarchive_calibre_group(self):
        calibre_group = ObsoleteCalibreGroupFactory(is_active=False)
        calibre_group.unarchive()
        self.assertTrue(calibre_group.is_active)

    def test_string_representation(self):
        calibre_group = ObsoleteCalibreGroupFactory(name="Test")
        self.assertEqual(calibre_group.__str__(), "Obsolete Calibre Group (Test)")


class ObsoleteCalibreTest(TestCase):
    def test_create_calibre(self):
        calibre = ObsoleteCalibreFactory(name="Test Calibre", order=1)
        self.assertTrue(isinstance(calibre, ObsoleteCalibre))
        self.assertEqual(calibre.name, "Test Calibre")
        self.assertEqual(calibre.order, 1)

    def test_archive_calibre(self):
        calibre = ObsoleteCalibreFactory(is_active=True)
        calibre.archive()
        self.assertFalse(calibre.is_active)

    def test_unarchive_calibre(self):
        calibre = ObsoleteCalibreFactory(is_active=False)
        calibre.unarchive()
        self.assertTrue(calibre.is_active)

    def test_status(self):
        calibre = ObsoleteCalibre()
        calibre.name = "Test Calibre"
        calibre.order = 1
        calibre.calibre_group = ObsoleteCalibreGroupFactory()
        self.assertEqual(calibre.status, "Pending")
        calibre.save()
        self.assertEqual(calibre.status, "Current")
        calibre.archive()
        self.assertEqual(calibre.status, "Archived")

    def test_string_representation(self):
        calibre = ObsoleteCalibreFactory(name="Test")
        self.assertEqual(calibre.__str__(), "Obsolete Calibre (Test)")
