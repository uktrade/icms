from django.test import TestCase
from web.domains.case.fir.forms import FurtherInformationRequestForm, FurtherInformationRequestDisplayForm
from web.domains.case.fir.models import FurtherInformationRequest


class FurtherInformationRequestFormTest(TestCase):
    def test_get_top_buttons(self):
        form = FurtherInformationRequestForm()
        self.assertEqual(['save'], form.get_top_buttons())

    def test_get_bottom_buttons(self):
        form = FurtherInformationRequestForm()
        self.assertEqual(['send', 'delete'], form.get_bottom_buttons())


class FurtherInformationRequestDisplayFormTest(TestCase):
    def setUp(self):
        form = FurtherInformationRequestDisplayForm()
        fir = FurtherInformationRequest()
        form.instance = fir

        self.form = form

    def test_get_top_buttons(self):
        self.form.instance.status = FurtherInformationRequest.OPEN
        self.assertEqual([], self.form.get_top_buttons())

        self.form.instance.status = FurtherInformationRequest.DRAFT
        self.assertEqual(['edit'], self.form.get_top_buttons())

    def test_get_bottom_buttons(self):
        self.form.instance.status = FurtherInformationRequest.DRAFT
        self.assertEqual([], self.form.get_bottom_buttons())

        self.form.instance.status = FurtherInformationRequest.OPEN
        self.assertEqual(['withdraw'], self.form.get_bottom_buttons())
