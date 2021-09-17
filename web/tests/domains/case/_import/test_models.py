import pytest
from django.test import TestCase

from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.flow.models import Process
from web.models import (
    DerogationsApplication,
    DFLApplication,
    IronSteelApplication,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    PriorSurveillanceApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    TextilesApplication,
    WoodQuotaApplication,
)
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.office.factory import OfficeFactory
from web.tests.domains.template.factory import TemplateFactory
from web.tests.domains.user.factory import UserFactory


class ImportApplicationTypeTest(TestCase):
    def create_application_type(self):
        return ImportApplicationType.objects.create(
            is_active=True,
            type="TEST",
            sub_type="TEST",
            licence_type_code="TEST",
            sigl_flag=True,
            chief_flag=True,
            paper_licence_flag=False,
            electronic_licence_flag=False,
            cover_letter_flag=False,
            cover_letter_schedule_flag=False,
            category_flag=True,
            endorsements_flag=True,
            quantity_unlimited_flag=True,
            exp_cert_upload_flag=False,
            supporting_docs_upload_flag=False,
            multiple_commodities_flag=False,
            usage_auto_category_desc_flag=True,
            case_checklist_flag=True,
            importer_printable=True,
            declaration_template=TemplateFactory(is_active=True),
        )

    def test_create_application_type(self):
        application_type = self.create_application_type()
        self.assertTrue(isinstance(application_type, ImportApplicationType))
        self.assertEqual(application_type.type, "TEST")
        self.assertEqual(application_type.sub_type, "TEST")


class ImportApplicationTest(TestCase):
    def create_import_application(self):
        importer = ImporterFactory(
            offices=(OfficeFactory(is_active=True), OfficeFactory(is_active=True))
        )

        return ImportApplication.objects.create(
            process_type=SanctionsAndAdhocApplication.PROCESS_TYPE,
            is_active=True,
            application_type=ImportApplicationType.objects.get(
                type=ImportApplicationType.Types.SANCTION_ADHOC
            ),
            created_by=UserFactory(is_active=True),
            last_updated_by=UserFactory(is_active=True),
            importer=importer,
            importer_office=importer.offices.first(),
        )

    def test_create_import_application(self):
        application = self.create_import_application()
        self.assertTrue(isinstance(application, ImportApplication))


@pytest.mark.parametrize(
    "application_model",
    [
        DerogationsApplication,
        DFLApplication,
        IronSteelApplication,
        OpenIndividualLicenceApplication,
        OutwardProcessingTradeApplication,
        PriorSurveillanceApplication,
        SanctionsAndAdhocApplication,
        SILApplication,
        TextilesApplication,
        WoodQuotaApplication,
    ],
)
@pytest.mark.django_db
def test_import_downcast(application_model, importer, test_import_user):
    obj = application_model.objects.create(
        # this is not important for this test, so just hardcode it
        application_type=ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.WOOD_QUOTA
        ),
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=importer.offices.first(),
        process_type=application_model.PROCESS_TYPE,
    )

    # if we already have the specific model, downcast should be a no-op
    assert id(obj) == id(obj.get_specific_model())

    # if we don't, it should load the correct type from the db, and it should be a new instance
    p = Process.objects.get(pk=obj.pk)

    downcast = p.get_specific_model()
    assert type(downcast) is application_model
    assert id(obj) != id(downcast)
