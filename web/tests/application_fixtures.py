import datetime as dt
from typing import Any, TypeAlias

from django.test import RequestFactory
from freezegun import freeze_time

from web.domains.case.services import case_progress, document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.utils import submit_application
from web.domains.template.utils import add_template_data_on_submit
from web.middleware.common import ICMSMiddlewareContext
from web.models import (
    Commodity,
    Constabulary,
    Country,
    DFLApplication,
    DFLGoodsCertificate,
    DFLSupplementaryInfo,
    File,
    ImportApplicationType,
    Importer,
    Office,
    OILSupplementaryInfo,
    OpenIndividualLicenceApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    Task,
    User,
    UserImportCertificate,
    WoodContractFile,
    WoodQuotaApplication,
)
from web.models.shared import FirearmCommodity
from web.utils.commodity import get_active_commodities

IA_TYPES = ImportApplicationType.Types
IA_SUB_TYPES = ImportApplicationType.SubTypes

IMPORT_APPS: TypeAlias = (
    WoodQuotaApplication
    | SanctionsAndAdhocApplication
    | SILApplication
    | DFLApplication
    | OpenIndividualLicenceApplication
)


class ImportAppFixtureBase:
    def __init__(
        self,
        rf: RequestFactory,
        importer: Importer,
        office: Office,
        app_contact: User,
        agent_importer: Importer | None = None,
        agent_office: Office | None = None,
    ) -> None:
        self.rf = rf
        self.importer = importer
        self.office = office
        self.app_contact = app_contact
        self.agent_importer = agent_importer
        self.agent_office = agent_office

    def _create_app(
        self,
        cls: type[IMPORT_APPS],
        t: ImportApplicationType.Types,
        st: ImportApplicationType.SubTypes = None,
    ) -> IMPORT_APPS:
        kwargs = {"type": t}
        if st:
            kwargs["sub_type"] = st

        app_type = ImportApplicationType.objects.get(**kwargs)
        application = cls.objects.create(
            process_type=cls.PROCESS_TYPE,
            application_type=app_type,
            importer=self.importer,
            importer_office=self.office,
            agent=self.agent_importer,
            agent_office=self.agent_office,
            created_by=self.app_contact,
            last_updated_by=self.app_contact,
            status=ImpExpStatus.IN_PROGRESS,
            contact=self.app_contact,
        )

        document_pack.pack_draft_create(application)

        return application

    def _set_in_progress_status_and_task(self, application: IMPORT_APPS) -> None:
        application.status = ImpExpStatus.IN_PROGRESS
        application.save()

        Task.objects.create(
            process=application, task_type=Task.TaskType.PREPARE, owner=self.app_contact
        )

    def _submit_application(self, application: IMPORT_APPS) -> None:
        self.rf.user = self.app_contact
        self.rf.icms = ICMSMiddlewareContext()

        # Submit application
        task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)
        with freeze_time("2024-01-01 12:00:00"):
            submit_application(application, self.rf, task)

        add_template_data_on_submit(application)


class WoodAppFixture(ImportAppFixtureBase):
    def in_progress(self) -> WoodQuotaApplication:
        wood_app = self._create_app(WoodQuotaApplication, IA_TYPES.WOOD_QUOTA)

        wood_commodities = get_active_commodities(
            Commodity.objects.filter(commodity_type__type="Wood")
        )

        wood_app.applicant_reference = "Wood App Reference"
        wood_app.shipping_year = dt.date.today().year
        wood_app.exporter_name = "Some Exporter"
        wood_app.exporter_address = "Some Exporter Address"
        wood_app.exporter_vat_nr = "123456789"
        wood_app.commodity = wood_commodities.first()
        wood_app.goods_description = "Very Woody"
        wood_app.goods_qty = 43
        wood_app.goods_unit = "cubic metres"
        wood_app.additional_comments = "Nothing more to say"
        wood_app.save()

        # Add a contract file
        wood_app.contract_documents.add(
            add_dummy_file(
                WoodContractFile, reference="reference field", contract_date="2021-11-09"
            )
        )

        # Set correct task
        self._set_in_progress_status_and_task(wood_app)

        return wood_app

    def submitted(self) -> WoodQuotaApplication:
        wood_app = self.in_progress()
        self._submit_application(wood_app)

        return wood_app


class FirearmsDFLAppFixture(ImportAppFixtureBase):
    def in_progress(self) -> DFLApplication:
        dfl_app = self._create_app(DFLApplication, IA_TYPES.FIREARMS, IA_SUB_TYPES.DFL)

        dfl_countries = Country.util.get_all_countries()
        origin_country = dfl_countries[0]
        consignment_country = dfl_countries[1]
        constabulary = Constabulary.objects.get(name="Derbyshire")
        dfl_app.applicant_reference = "applicant_reference value"
        dfl_app.deactivated_firearm = True
        dfl_app.proof_checked = True
        dfl_app.origin_country = origin_country
        dfl_app.consignment_country = consignment_country
        dfl_app.commodity_code = FirearmCommodity.EX_CHAPTER_93.value
        dfl_app.constabulary = constabulary
        dfl_app.know_bought_from = False
        dfl_app.save()

        # Add a contract file
        issuing_country = Country.app.get_fa_dfl_issuing_countries().first()
        dfl_app.goods_certificates.add(
            add_dummy_file(
                DFLGoodsCertificate,
                goods_description="goods_description value",
                goods_description_original="goods_description value",
                deactivated_certificate_reference="deactivated_certificate_reference value",
                issuing_country=issuing_country,
            )
        )

        # Set correct task
        self._set_in_progress_status_and_task(dfl_app)

        return dfl_app

    def submitted(self) -> DFLApplication:
        dfl_app = self.in_progress()
        self._submit_application(dfl_app)
        DFLSupplementaryInfo.objects.create(import_application=dfl_app)

        return dfl_app


class FirearmsOILAppFixture(ImportAppFixtureBase):
    def in_progress(self) -> OpenIndividualLicenceApplication:
        oil_app = self._create_app(
            OpenIndividualLicenceApplication, IA_TYPES.FIREARMS, IA_SUB_TYPES.OIL
        )

        any_country = Country.objects.get(name="Any Country", is_active=True)

        oil_app.applicant_reference = "applicant_reference value"
        oil_app.section1 = True
        oil_app.section2 = True
        oil_app.origin_country = any_country
        oil_app.consignment_country = any_country
        oil_app.commodity_code = "ex Chapter 93"
        oil_app.know_bought_from = False
        oil_app.save()

        oil_app.user_imported_certificates.add(
            add_dummy_file(
                UserImportCertificate,
                reference="Certificate Reference Value",
                certificate_type="registered",
                constabulary=Constabulary.objects.first(),
                date_issued=dt.date.today(),
                expiry_date=dt.date.today(),
            )
        )

        # Set correct task
        self._set_in_progress_status_and_task(oil_app)

        return oil_app

    def submitted(self) -> OpenIndividualLicenceApplication:
        oil_app = self.in_progress()
        self._submit_application(oil_app)
        OILSupplementaryInfo.objects.create(import_application=oil_app)

        return oil_app


def add_dummy_file(cls: type[File], **kwargs: Any) -> File:
    return cls.objects.create(
        path="dummy-path",
        filename="dummy-filename",
        content_type="application/pdf",
        file_size=100,
        created_by_id=0,
        **kwargs,
    )
