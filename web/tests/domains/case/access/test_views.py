from django import forms
from django.test import TestCase

from web.domains.case.access.models import AccessRequest
from web.domains.case.access.views import clean_extra_request_data
from web.domains.case.fir.forms import (FurtherInformationRequestDisplayForm,
                                        FurtherInformationRequestForm)
from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.fir.views import AccessRequestFirView
from web.tests.domains.case.fir.factory import FurtherInformationRequestFactory


def populate_fields(access_request):
    access_request.agent_name = 'Agent Smith'
    access_request.agent_address = '50 VS'
    access_request.request_reason = 'Import/Export'


class AccessRequestViewsTest(TestCase):
    def test_missing_request_type(self):
        access_request = AccessRequest()
        self.assertRaises(ValueError, clean_extra_request_data, access_request)

    def test_unknown_request_type(self):
        access_request = AccessRequest()
        access_request.request_type = "ADMIN_ACCESS"
        self.assertRaises(ValueError, clean_extra_request_data, access_request)

    def test_importer(self):
        access_request = AccessRequest()
        access_request.request_type = AccessRequest.IMPORTER
        populate_fields(access_request)

        clean_extra_request_data(access_request)

        self.assertIsNone(access_request.agent_name)
        self.assertIsNone(access_request.agent_address)

    def test_exporter(self):
        access_request = AccessRequest()
        access_request.request_type = AccessRequest.EXPORTER
        populate_fields(access_request)

        clean_extra_request_data(access_request)

        self.assertIsNone(access_request.request_reason)
        self.assertIsNone(access_request.agent_name)
        self.assertIsNone(access_request.agent_address)

    def test_exporter_agent(self):
        access_request = AccessRequest()
        access_request.request_type = AccessRequest.EXPORTER_AGENT
        populate_fields(access_request)

        clean_extra_request_data(access_request)

        self.assertIsNone(access_request.request_reason)


class AccessRequestFirViewTest(TestCase):
    def setUp(self):
        self.view = AccessRequestFirView()

        self.model = FurtherInformationRequestFactory()

    def test_set_fir_status(self):
        """
        Asserts FIR has the status changes sucessfully
        """
        self.assertEqual(FurtherInformationRequest.DRAFT, self.model.status)
        model = self.view.set_fir_status(self.model.pk,
                                         FurtherInformationRequest.OPEN)
        self.assertEqual(FurtherInformationRequest.OPEN, model.status)

    def test_create_display_or_edit_form_return_edit_form(self):
        """
        Asserts that when the fir id matches the id passed an edit form is returned
        """
        form = self.view.create_display_or_edit_form(self.model, self.model.pk,
                                                     None)
        self.assertIsInstance(form, FurtherInformationRequestForm)
        self.assertEqual(form.instance, self.model)

    def test_create_display_or_edit_form_return_passed_form(self):
        """
        Asserts that when the fir id matches the id passed and a return object is passed, that object is returned
        """
        expected_return_class = forms.Form
        form = self.view.create_display_or_edit_form(self.model, self.model.pk,
                                                     expected_return_class())
        self.assertIsInstance(form, expected_return_class)

    def test_create_display_or_edit_form_return_display_form(self):
        """
        Asserts that when the fir id DO NOT match the id passed a display form is returned
        """
        form = self.view.create_display_or_edit_form(self.model,
                                                     self.model.pk + 1, None)
        self.assertIsInstance(form, FurtherInformationRequestDisplayForm)
        self.assertEqual(form.instance, self.model)
