import logging

from django.test import TestCase
from guardian.shortcuts import assign_perm

from web.domains.case._import.forms import CreateOILForm
from web.tests.domains.case._import.factory import OILApplicationFactory
from web.tests.domains.importer.factory import AgentImporterFactory, ImporterFactory
from web.tests.domains.office.factory import OfficeFactory
from web.tests.domains.user.factory import ActiveUserFactory

logger = logging.getLogger(__name__)


class TestCreateOpenIndividualImportLicenceForm(TestCase):
    def setUp(self):
        OILApplicationFactory.create()

    def test_form_valid(self):
        office = OfficeFactory.create(is_active=True)
        importer = ImporterFactory.create(is_active=True, offices=[office])
        contact = ActiveUserFactory.create()
        assign_perm("web.is_contact_of_importer", contact, importer)

        form = CreateOILForm(
            contact,
            data={
                "importer": importer.pk,
                "importer_office": office.pk,
            },
        )
        self.assertTrue(form.is_valid())

    def test_agent_form_valid(self):
        office = OfficeFactory.create(is_active=True)
        agent_importer = AgentImporterFactory(main_importer_offices=[office])
        agent = ActiveUserFactory.create()
        assign_perm("web.is_agent_of_importer", agent, agent_importer.main_importer)

        form = CreateOILForm(
            agent,
            data={
                "importer": agent_importer.main_importer.pk,
                "importer_office": office.pk,
            },
        )
        self.assertTrue(form.is_valid())

    def test_invalid_form_message(self):
        office = OfficeFactory.create(is_active=True)
        importer = ImporterFactory.create(is_active=True, offices=[office])
        contact = ActiveUserFactory.create()
        assign_perm("web.is_contact_of_importer", contact, importer)

        form = CreateOILForm(contact, data={})
        logger.debug(form.errors)
        self.assertEqual(len(form.errors), 2)
        message = form.errors["importer"][0]
        self.assertEqual(message, "You must enter this item")
