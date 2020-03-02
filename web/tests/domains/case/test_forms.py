from django.test import TestCase
from web.domains.case.forms import FurtherInformationRequestForm, FurtherInformationRequestDisplayForm
from web.domains.case.models import FurtherInformationRequest


class FurtherInformationRequestFormTest(TestCase):
    def test_get_top_buttons(self):
        form = FurtherInformationRequestForm()
        self.assertEquals(['save'], form.get_top_buttons())

    def test_get_bottom_buttons(self):
        form = FurtherInformationRequestForm()
        self.assertEquals(['send', 'delete'], form.get_bottom_buttons())


class FurtherInformationRequestDisplayFormTest(TestCase):

    def setUp(self):
        form = FurtherInformationRequestDisplayForm()
        fir = FurtherInformationRequest()
        form.instance = fir

        self.form = form

    def test_get_top_buttons(self):
        self.form.instance.status = FurtherInformationRequest.OPEN
        self.assertEquals([], self.form.get_top_buttons())

        self.form.instance.status = FurtherInformationRequest.DRAFT
        self.assertEquals(['edit'], self.form.get_top_buttons())

    def test_get_bottom_buttons(self):
        self.form.instance.status = FurtherInformationRequest.DRAFT
        self.assertEquals([], self.form.get_bottom_buttons())

        self.form.instance.status = FurtherInformationRequest.OPEN
        self.assertEquals(['withdraw'], self.form.get_bottom_buttons())
