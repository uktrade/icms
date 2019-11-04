import logging
from django.test import RequestFactory, TestCase
from django.urls import reverse_lazy
from web.domains.application._import.forms import NewImportApplicationForm
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.user.factory import UserFactory
from web.tests.domains.office.factory import OfficeFactory

from .factory import ImportApplicationTypeFactory

logger = logging.getLogger(__name__)


class NewImportApplicationFormTest(TestCase):
    def setUp(self):
        self.user = UserFactory(is_active=True)
        self.type = ImportApplicationTypeFactory(is_active=True)
        self.office = OfficeFactory(is_active=True)
        self.request = RequestFactory().post(
            reverse_lazy('import_application_new'))
        self.request.user = self.user

    def create_importer(self, main_importer=None):
        importer = ImporterFactory(main_importer=main_importer, is_active=True)
        importer.members.add(self.user)
        importer.offices.add(self.office)
        return importer

    def test_main_importer_form_valid(self):
        importer = self.create_importer()
        form = NewImportApplicationForm(self.request,
                                        data={
                                            'application_type': self.type.pk,
                                            'importer': importer.pk,
                                            'importer_office': self.office.pk
                                        })
        self.assertTrue(form.is_valid())

    def test_importer_agent_form_valid(self):
        main_importer = ImporterFactory(is_active=True, main_importer=None)
        office = OfficeFactory(is_active=True)
        main_importer.offices.add(office)
        agent = self.create_importer(main_importer=main_importer)
        form = NewImportApplicationForm(self.request,
                                        data={
                                            'application_type': self.type.pk,
                                            'importer': main_importer.pk,
                                            'importer_office': office.pk,
                                            'agent': agent.pk
                                        })
        self.assertTrue(form.fields['agent'])
        self.assertTrue(form.is_valid())

    def test_agent_is_in_the_form(self):
        main_importer = ImporterFactory(is_active=True, main_importer=None)
        self.create_importer(main_importer=main_importer)  # Create agent
        form = NewImportApplicationForm(self.request,
                                        data={
                                            'application_type': self.type.pk,
                                            'importer': main_importer.pk
                                        })

        self.assertTrue(form.fields['agent'])

    def test_derogations_application_now_allowed_for_agents(self):
        main_importer = ImporterFactory(is_active=True, main_importer=None)
        self.create_importer(main_importer=main_importer)  # Create agent
        derogations_application = ImportApplicationTypeFactory(
            type='Derogation from Sanctions Import Ban')
        form = NewImportApplicationForm(self.request,
                                        data={
                                            'application_type':
                                            derogations_application.pk,
                                            'importer':
                                            main_importer.pk
                                        })
        self.assertFalse('agent' in form.fields.keys())

    def test_invalid_form_message(self):
        form = NewImportApplicationForm(
            self.request, data={'application_type': self.type.pk})
        logger.debug(form.errors)
        self.assertEqual(len(form.errors), 2)
        message = form.errors['importer'][0]
        self.assertEqual(message, 'You must enter this item')
