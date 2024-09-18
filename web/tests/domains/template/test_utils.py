import datetime as dt
from unittest.mock import Mock

import pytest

from web.domains.case.services import document_pack
from web.domains.template.context import CoverLetterTemplateContext
from web.domains.template.utils import (
    ScheduleParagraphs,
    ScheduleText,
    add_application_default_cover_letter,
    add_endorsements_from_application_type,
    add_template_data_on_submit,
    fetch_schedule_text,
    find_invalid_placeholders,
    get_application_update_template_data,
    get_context_dict,
    get_cover_letter_content,
    get_fir_template_data,
    get_letter_fragment,
)
from web.models import (
    CertificateOfManufactureApplication,
    CFSSchedule,
    Country,
    DFLApplication,
    EndorsementImportApplication,
    ExportApplicationType,
    FurtherInformationRequest,
    ImportApplicationType,
    Office,
    OpenIndividualLicenceApplication,
    ProductLegislation,
    SanctionsAndAdhocApplication,
    SILApplication,
    Template,
)
from web.models.shared import YesNoChoices
from web.tests.helpers import CaseURLS
from web.types import DocumentTypes
from web.views.actions import EditTemplate


def _create_pack_documents(app):
    if app.status in ["IN_PROGRESS", "SUBMITTED", "COMPLETED"]:
        doc_pack = document_pack.pack_draft_create(app)
        doc_pack.licence_start_date = dt.date.today()
        doc_pack.licence_end_date = dt.date(dt.date.today().year + 1, 12, 1)
        doc_pack.save()
        document_pack.doc_ref_documents_create(app, lock_manager=Mock())

    if app.status == "COMPLETED":
        document_pack.pack_draft_set_active(app)


def _create_sil_app(importer_one_contact, importer, office, extra=None):
    """Creates a SIL app with default data overridable with extra"""
    if not extra:
        extra = {}

    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.SIL
    )

    sil_data = {
        "created_by": importer_one_contact,
        "last_updated_by": importer_one_contact,
        "importer": importer,
        "importer_office": office,
        "process_type": SILApplication.PROCESS_TYPE,
        "application_type": application_type,
        "contact": importer_one_contact,
        "submit_datetime": dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.UTC),
    } | extra

    app = SILApplication.objects.create(**sil_data)

    return app


def _create_dfl_app(importer_one_contact, importer, office, extra=None):
    if not extra:
        extra = {}

    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    dfl_data = {
        "created_by": importer_one_contact,
        "last_updated_by": importer_one_contact,
        "importer": importer,
        "importer_office": office,
        "process_type": DFLApplication.PROCESS_TYPE,
        "application_type": application_type,
        "contact": importer_one_contact,
        "submit_datetime": dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.UTC),
        "status": "IN_PROGRESS",
        "consignment_country": Country.objects.get(name="Germany"),
        "origin_country": Country.objects.get(name="Albania"),
    } | extra

    app = DFLApplication.objects.create(**dfl_data)
    _create_pack_documents(app)

    return app


def _create_com_app(exporter_one_contact, exporter, office, extra=None):
    """Creates a COM app with default data overridable with extra"""
    if not extra:
        extra = {}

    application_type = ExportApplicationType.objects.get(
        type_code=ExportApplicationType.Types.MANUFACTURE
    )

    com_data = {
        "created_by": exporter_one_contact,
        "last_updated_by": exporter_one_contact,
        "exporter": exporter,
        "exporter_office": office,
        "process_type": CertificateOfManufactureApplication.PROCESS_TYPE,
        "application_type": application_type,
        "contact": exporter_one_contact,
        "submit_datetime": dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.UTC),
        "status": "SUBMITTED",
    } | extra

    app = CertificateOfManufactureApplication.objects.create(**com_data)
    app.countries.add(Country.objects.get(name="Germany"))
    app.countries.add(Country.objects.get(name="Albania"))

    _create_pack_documents(app)

    return app


def test_add_endorsements_from_application_type(importer_one_contact, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    active_endorsement = Template.objects.filter(
        template_type=Template.ENDORSEMENT, is_active=True
    ).first()

    # Add active endorsement to application type
    application_type.endorsements.add(active_endorsement)

    inactive_endorsement = Template.objects.filter(
        template_type=Template.ENDORSEMENT, is_active=False
    ).first()

    # Add inactive endorsement to application type
    application_type.endorsements.add(inactive_endorsement)
    app = _create_dfl_app(importer_one_contact, importer, office)
    add_endorsements_from_application_type(app)

    # Check application only includes active endorsements from application type
    assert app.endorsements.count() == 2
    assert active_endorsement.template_content in app.endorsements.values_list("content", flat=True)


def test_add_endorsements_from_application_type_added(importer_one_contact, importer, office):
    # Add active endorsements to application type
    app = _create_dfl_app(importer_one_contact, importer, office)

    # Add endorsement to application
    EndorsementImportApplication.objects.create(
        import_application_id=app.pk, content="Test Content"
    )
    add_endorsements_from_application_type(app)

    # Check only endorsement that was one the application is still on the application
    assert app.endorsements.count() == 1
    assert list(app.endorsements.values_list("content", flat=True)) == ["Test Content"]


def test_add_template_data_on_submit(importer_one_contact, importer, office):
    app = _create_dfl_app(importer_one_contact, importer, office)
    template = Template.objects.get(
        template_code=Template.Codes.COVER_FIREARMS_DEACTIVATED_FIREARMS
    )

    add_template_data_on_submit(app)

    # Check application only includes active endorsements from application type
    assert app.endorsements.count() == 1
    assert app.cover_letter_text == template.template_content


def test_get_cover_letter_context(importer_one_contact, importer, office):
    app = _create_dfl_app(
        importer_one_contact,
        importer,
        office,
        extra={"submit_datetime": dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.UTC)},
    )

    template_text = """
    Hello [[CONTACT_NAME]], [[APPLICATION_SUBMITTED_DATE]], [[COUNTRY_OF_CONSIGNMENT]]
    [[COUNTRY_OF_ORIGIN]] [[LICENCE_NUMBER]] [[LICENCE_END_DATE]]
    """

    context = CoverLetterTemplateContext(app, DocumentTypes.COVER_LETTER_PREVIEW)
    context_dict = get_context_dict(template_text, context)

    assert context_dict["APPLICATION_SUBMITTED_DATE"] == "25 December 2022"
    assert context_dict["CONTACT_NAME"] == importer_one_contact.full_name
    assert context_dict["COUNTRY_OF_CONSIGNMENT"] == "Germany"
    assert context_dict["COUNTRY_OF_ORIGIN"] == "Albania"
    assert context_dict["LICENCE_NUMBER"] == '<span class="placeholder">[[LICENCE_NUMBER]]</span>'
    assert (
        context_dict["LICENCE_END_DATE"] == '<span class="placeholder">[[LICENCE_END_DATE]]</span>'
    )

    doc_pack = document_pack.pack_draft_get(app)
    context = CoverLetterTemplateContext(app, DocumentTypes.COVER_LETTER_PRE_SIGN)
    context_dict = get_context_dict(template_text, context)

    assert context_dict["APPLICATION_SUBMITTED_DATE"] == "25 December 2022"
    assert context_dict["CONTACT_NAME"] == importer_one_contact.full_name
    assert context_dict["COUNTRY_OF_CONSIGNMENT"] == "Germany"
    assert context_dict["COUNTRY_OF_ORIGIN"] == "Albania"
    assert context_dict["LICENCE_NUMBER"] == document_pack.doc_ref_licence_get(doc_pack).reference
    assert context_dict["LICENCE_END_DATE"] == "01 December " + str(dt.date.today().year + 1)

    context = CoverLetterTemplateContext(app, DocumentTypes.COVER_LETTER_SIGNED)
    context_dict = get_context_dict(template_text, context)

    assert context_dict["APPLICATION_SUBMITTED_DATE"] == "25 December 2022"
    assert context_dict["CONTACT_NAME"] == importer_one_contact.full_name
    assert context_dict["COUNTRY_OF_CONSIGNMENT"] == "Germany"
    assert context_dict["COUNTRY_OF_ORIGIN"] == "Albania"
    assert context_dict["LICENCE_NUMBER"] == document_pack.doc_ref_licence_get(doc_pack).reference
    assert context_dict["LICENCE_END_DATE"] == "01 December " + str(dt.date.today().year + 1)

    context = CoverLetterTemplateContext(app, DocumentTypes.CERTIFICATE_PREVIEW)

    with pytest.raises(ValueError, match=r"CERTIFICATE_PREVIEW is not a valid document type"):
        get_context_dict(template_text, context)


def test_get_cover_letter_invalid_context(importer_one_contact, importer, office):
    app = _create_dfl_app(importer_one_contact, importer, office)
    template_text = "Hello [[INVALID]]"
    context = CoverLetterTemplateContext(app, DocumentTypes.COVER_LETTER_PREVIEW)

    with pytest.raises(
        ValueError, match=r"INVALID is not a valid cover letter template context value"
    ):
        get_context_dict(template_text, context)


def test_dfl_add_application_default_cover_letter(importer_one_contact, importer, office):
    app = _create_dfl_app(importer_one_contact, importer, office)
    template = Template.objects.get(
        template_code=Template.Codes.COVER_FIREARMS_DEACTIVATED_FIREARMS
    )

    add_application_default_cover_letter(app)
    assert app.cover_letter_text == template.template_content


def test_get_cover_letter_content(importer_one_contact, importer, office):
    app = _create_dfl_app(importer_one_contact, importer, office)
    content = get_cover_letter_content(app, DocumentTypes.COVER_LETTER_PREVIEW)

    assert content == ""

    app.cover_letter_text = "Hello [[CONTACT_NAME]]"
    content = get_cover_letter_content(app, DocumentTypes.COVER_LETTER_PREVIEW)
    assert content == "Hello " + str(importer_one_contact)


def test_oil_add_application_default_cover_letter(importer_one_contact, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.OIL
    )

    app = OpenIndividualLicenceApplication.objects.create(
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
        importer=importer,
        importer_office=office,
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=application_type,
        contact=importer_one_contact,
        submit_datetime=dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.UTC),
    )
    template = Template.objects.get(template_code=Template.Codes.COVER_FIREARMS_OIL)

    add_application_default_cover_letter(app)
    assert app.cover_letter_text == template.template_content


def test_sil_add_application_default_cover_letter(importer_one_contact, importer, office):
    app = _create_sil_app(importer_one_contact, importer, office)

    add_application_default_cover_letter(app)
    assert app.cover_letter_text is None


def test_sanctions_application_default_cover_letter(importer_one_contact, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.SANCTION_ADHOC
    )

    app = SanctionsAndAdhocApplication.objects.create(
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
        importer=importer,
        importer_office=office,
        process_type=SanctionsAndAdhocApplication.PROCESS_TYPE,
        application_type=application_type,
        contact=importer_one_contact,
        submit_datetime=dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.UTC),
    )

    with pytest.raises(
        ValueError, match=r"No default cover letter for SanctionsAndAdhocApplication"
    ):
        add_application_default_cover_letter(app)


def test_get_letter_fragment_dfl(importer_one_contact, importer, office):
    app = _create_dfl_app(importer_one_contact, importer, office)

    with pytest.raises(ValueError, match=r"No letter fragments for process type DFLApplication"):
        get_letter_fragment(app)


@pytest.mark.parametrize(
    "mp,eu,man",
    [(None, None, None), (None, False, False), (False, None, False), (False, False, None)],
)
def test_sil_incomplete_get_letter_fragment(importer_one_contact, importer, office, mp, eu, man):
    app = _create_sil_app(
        importer_one_contact,
        importer,
        office,
        extra={
            "military_police": mp,
            "eu_single_market": eu,
            "manufactured": man,
        },
    )

    with pytest.raises(
        ValueError, match=r"Unable to get letter fragment due to missing application data"
    ):
        get_letter_fragment(app)


@pytest.mark.parametrize(
    "mp,eu,man,tc",
    [
        (True, False, False, Template.Codes.FIREARMS_MARKINGS_NON_STANDARD),
        (False, True, False, Template.Codes.FIREARMS_MARKINGS_NON_STANDARD),
        (False, False, True, Template.Codes.FIREARMS_MARKINGS_NON_STANDARD),
        (False, False, False, Template.Codes.FIREARMS_MARKINGS_STANDARD),
    ],
)
def test_sil_get_letter_fragment(importer_one_contact, importer, office, mp, eu, man, tc):
    app = _create_sil_app(
        importer_one_contact,
        importer,
        office,
        extra={
            "military_police": mp,
            "eu_single_market": eu,
            "manufactured": man,
        },
    )

    template = Template.objects.get(template_code=tc)
    assert get_letter_fragment(app) == template.template_content


@pytest.mark.parametrize(
    "content,placeholders,expected",
    [
        ("Some content", ["ONE", "TWO", "THREE"], []),
        ("Some content [[ONE]]", ["ONE", "TWO", "THREE"], []),
        ("Some content [[FOUR]]", ["ONE", "TWO", "THREE"], ["[[FOUR]]"]),
        ("Some content", [], []),
        ("Some content [[ONE]]", [], ["[[ONE]]"]),
    ],
)
def test_find_invalid_placeholders(content, placeholders, expected):
    assert find_invalid_placeholders(content, placeholders) == expected


def test_get_import_application_update_request_contents(wood_app_submitted, ilb_admin_two):
    _check_get_export_application_update_request_contents(wood_app_submitted, ilb_admin_two)


def test_get_export_application_update_request_contents(com_app_submitted, ilb_admin_two):
    _check_get_export_application_update_request_contents(com_app_submitted, ilb_admin_two)


def _check_get_export_application_update_request_contents(app, case_owner):
    app.case_owner = case_owner
    actual_subject, actual_body = get_application_update_template_data(app)
    assert actual_subject == f"Request for updates to your application {app.reference}"
    assert "You need to update your application with the following information" in actual_body


def test_get_error_application_update_request_contents(ilb_admin_user):
    fir = FurtherInformationRequest.objects.create(
        process_type=FurtherInformationRequest.PROCESS_TYPE,
        requested_by=ilb_admin_user,
        status=FurtherInformationRequest.DRAFT,
        request_subject="test subject",
        request_detail="test request detail",
    )

    with pytest.raises(
        ValueError,
        match=r"Application must be an instance of ImportApplication / ExportApplication",
    ):
        get_application_update_template_data(fir)


def test_get_fir_template_data_import(fa_sil_app_submitted, ilb_admin_client, ilb_admin_user):
    app = fa_sil_app_submitted
    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))
    app.refresh_from_db()

    subject, body = get_fir_template_data(app, ilb_admin_user)

    assert subject == f"Request for more information {app.reference}"
    assert "You need to provide some more information" in body


def test_get_fir_template_data_export(gmp_app_submitted, ilb_admin_client, ilb_admin_user):
    app = gmp_app_submitted
    ilb_admin_client.post(CaseURLS.take_ownership(app.pk, "export"))
    app.refresh_from_db()

    subject, body = get_fir_template_data(app, ilb_admin_user)

    assert subject == f"Request for more information {app.reference}"
    assert "Some more information is needed" in body


def test_get_fir_template_data_importer_access(importer_access_request, ilb_admin_user):
    app = importer_access_request
    subject, body = get_fir_template_data(app, ilb_admin_user)

    assert subject == f"Request for more information {app.reference}"
    assert "Some more information is needed" in body


def test_get_fir_template_data_exporter_access(exporter_access_request, ilb_admin_user):
    app = exporter_access_request
    subject, body = get_fir_template_data(app, ilb_admin_user)

    assert subject == f"Request for more information {app.reference}"
    assert "Some more information is needed" in body


def test_get_fir_template_data_error(ilb_admin_user):
    fir = FurtherInformationRequest.objects.create(
        process_type=FurtherInformationRequest.PROCESS_TYPE,
        requested_by=ilb_admin_user,
        status=FurtherInformationRequest.DRAFT,
        request_subject="test subject",
        request_detail="test request detail",
    )

    with pytest.raises(
        ValueError,
        match=r"Process must be an instance of ImportApplication / ExportApplication / AccessRequest",
    ):
        get_fir_template_data(fir, ilb_admin_user)


class TestCreateSchedule:

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.aerosol_pl = ProductLegislation.objects.get(
            name="Aerosol Dispensers Regulations 2009/ 2824 as applicable in GB",
        )
        self.biocide_pl = ProductLegislation.objects.get(
            name="Biocide Products Regulation 528/2012 (EU BPR)"
        )

    def test_create_schedule_paragraph_gb_manufacture_address(
        self, cfs_app_submitted, exporter_one_contact
    ):
        country = Country.objects.get(name="Germany")

        schedule = CFSSchedule.objects.create(
            application=cfs_app_submitted,
            exporter_status=CFSSchedule.ExporterStatus.IS_MANUFACTURER,
            brand_name_holder=YesNoChoices.yes,
            product_eligibility=CFSSchedule.ProductEligibility.SOLD_ON_UK_MARKET,
            goods_placed_on_uk_market=YesNoChoices.yes,
            goods_export_only=YesNoChoices.no,
            country_of_manufacture=country,
            manufacturer_name="Manufacturer Name",
            manufacturer_address="123 Manufacturer, Manufactureton",
            manufacturer_postcode="123456",
            schedule_statements_is_responsible_person=True,
            schedule_statements_accordance_with_standards=True,
            created_by=exporter_one_contact,
        )

        schedule.legislations.add(self.aerosol_pl)
        schedule.legislations.add(self.biocide_pl)

        template = Template.objects.get(template_type=Template.CFS_SCHEDULE)
        sp = ScheduleParagraphs(schedule, template)

        assert sp.header == "Schedule to Certificate of Free Sale"
        assert sp.introduction == (
            "TEST EXPORTER 1, of E1 ADDRESS LINE 1 E1 ADDRESS LINE 2 HG15DB has made the following "  # /PS-IGNORE
            "legal declaration in relation to the products listed in this schedule:"
        )
        assert sp.paragraph == (
            "I am the manufacturer. I am the responsible person as defined by the "
            "EU Cosmetics Regulation 1223/2009 and I am the person responsible for "
            "ensuring that the products listed in this schedule meet the safety "
            "requirements set out in the EU Cosmetics Regulation 1223/2009. I certify "
            "that these products meet the safety requirements set out under UK and EU "
            "legislation, specifically: Aerosol Dispensers Regulations 2009/ 2824 as "
            "applicable in GB, Biocide Products Regulation 528/2012 (EU BPR). "
            "These products are currently sold on the EU market. "
            "These products are manufactured in accordance with the Good Manufacturing Practice "
            "standards set out in UK and EU law The products were manufactured in Germany by "
            "Manufacturer Name at 123 MANUFACTURER, MANUFACTURETON 123456"
        )

    def test_create_schedule_paragraph_gb_manufacture_country(
        self, cfs_app_submitted, exporter_one_contact
    ):
        country = Country.objects.get(name="Germany")

        schedule = CFSSchedule.objects.create(
            application=cfs_app_submitted,
            exporter_status=CFSSchedule.ExporterStatus.IS_MANUFACTURER,
            brand_name_holder=YesNoChoices.yes,
            product_eligibility=CFSSchedule.ProductEligibility.SOLD_ON_UK_MARKET,
            goods_placed_on_uk_market=YesNoChoices.yes,
            goods_export_only=YesNoChoices.no,
            country_of_manufacture=country,
            manufacturer_name=None,
            manufacturer_address=None,
            manufacturer_postcode=None,
            schedule_statements_is_responsible_person=False,
            schedule_statements_accordance_with_standards=False,
            created_by=exporter_one_contact,
        )

        schedule.legislations.add(self.aerosol_pl)
        schedule.legislations.add(self.biocide_pl)

        template = Template.objects.get(template_type=Template.CFS_SCHEDULE)
        sp = ScheduleParagraphs(schedule, template)

        assert sp.header == "Schedule to Certificate of Free Sale"
        assert sp.introduction == (
            "TEST EXPORTER 1, of E1 ADDRESS LINE 1 E1 ADDRESS LINE 2 HG15DB has made the following "  # /PS-IGNORE
            "legal declaration in relation to the products listed in this schedule:"
        )
        assert sp.paragraph == (
            "I am the manufacturer. I certify that these products meet the safety requirements "
            "set out under UK and EU legislation, specifically: Aerosol Dispensers Regulations 2009/ 2824 as "
            "applicable in GB, Biocide Products Regulation 528/2012 (EU BPR). "
            "These products are currently sold on the EU market. "
            "The products were manufactured in Germany"
        )

    def test_create_schedule_paragraph_ni_manufacture_name(
        self, cfs_app_submitted, exporter_one_contact
    ):
        country = Country.objects.get(name="Spain")
        ni_office = Office.objects.filter(postcode__startswith="BT").first()
        cfs_app_submitted.exporter_office = ni_office

        schedule = CFSSchedule.objects.create(
            application=cfs_app_submitted,
            exporter_status=CFSSchedule.ExporterStatus.IS_NOT_MANUFACTURER,
            brand_name_holder=YesNoChoices.yes,
            product_eligibility=CFSSchedule.ProductEligibility.MEET_UK_PRODUCT_SAFETY,
            goods_placed_on_uk_market=YesNoChoices.no,
            goods_export_only=YesNoChoices.yes,
            country_of_manufacture=country,
            manufacturer_name="Manufacturer Name",
            schedule_statements_is_responsible_person=True,
            schedule_statements_accordance_with_standards=True,
            created_by=exporter_one_contact,
        )

        pl = ProductLegislation.objects.get(
            name="Chemicals (Hazard Information and Packaging for Supply) Regulations 2009"
        )
        schedule.legislations.add(pl)

        template = Template.objects.get(template_type=Template.CFS_SCHEDULE)
        sp = ScheduleParagraphs(schedule, template)

        assert sp.header == "Schedule to Certificate of Free Sale"
        assert sp.introduction == (
            "TEST EXPORTER 1, of I1 ADDRESS LINE 1 I1 ADDRESS LINE 2 BT180LZ has made the following "  # /PS-IGNORE
            "legal declaration in relation to the products listed in this schedule:"
        )
        assert sp.paragraph == (
            "I am not the manufacturer. I am the responsible person as defined by Regulation "
            "(EC) No 1223/2009 of the European Parliament and of the Council of 30 November "
            "2009 on cosmetic products and Cosmetic Regulation No 1223/2009 as applicable in "
            "NI. I am the person responsible for ensuring that the products listed in this "
            "schedule meet the safety requirements set out in the Regulations. I certify that "
            "these products meet the safety requirements set out under UK and EU legislation, "
            "specifically: Chemicals (Hazard Information and Packaging for Supply) Regulations "
            "2009. These products meet the product safety requirements to be sold on the EU market. "
            "These products are manufactured in accordance with the Good Manufacturing Practice "
            "standards set out in UK or EU law where applicable The products were manufactured "
            "in Spain by Manufacturer Name"
        )

    def test_create_schedule_paragraph_translation(self, cfs_app_submitted, exporter_one_contact):
        country = Country.objects.get(name="Germany")

        schedule = CFSSchedule.objects.create(
            application=cfs_app_submitted,
            exporter_status=CFSSchedule.ExporterStatus.IS_MANUFACTURER,
            brand_name_holder=YesNoChoices.yes,
            product_eligibility=CFSSchedule.ProductEligibility.SOLD_ON_UK_MARKET,
            goods_placed_on_uk_market=YesNoChoices.yes,
            goods_export_only=YesNoChoices.no,
            country_of_manufacture=country,
            manufacturer_name="Manufacturer Name",
            manufacturer_address="123 Manufacturer, Manufactureton",
            manufacturer_postcode="123456",
            schedule_statements_is_responsible_person=True,
            schedule_statements_accordance_with_standards=True,
            created_by=exporter_one_contact,
        )
        schedule.legislations.add(self.aerosol_pl)
        schedule.legislations.add(self.biocide_pl)

        template = Template.objects.get(
            template_type=Template.CFS_SCHEDULE_TRANSLATION,
            template_code=Template.Codes.CFS_SCHEDULE_TRANSLATION,
            template_name="Spanish CFS Schedule",
        )
        sp = ScheduleParagraphs(schedule, template)

        assert sp.header == "Horario para el Certificado de Libre Venta"
        assert sp.introduction == (
            "TEST EXPORTER 1, de E1 ADDRESS LINE 1 E1 ADDRESS LINE 2 HG15DB ha hecho la siguiente declaración "  # /PS-IGNORE
            "legal en relación con los productos enumerados en este cronograma:"
        )
        assert sp.paragraph == (
            "Yo soy el fabricante. Soy la persona responsable según lo definido por el Reglamento "
            "de cosméticos n. ° 1223/2009 según se aplique en GB. Soy la persona responsable de "
            "garantizar que los productos enumerados en este programa cumplan con los requisitos "
            "de seguridad establecidos en ese Reglamento. Certifico que estos productos cumplen "
            "con los requisitos de seguridad establecidos en esta legislación: Aerosol Dispensers "
            "Regulations 2009/ 2824 as applicable in GB, Biocide Products Regulation 528/2012 "
            "(EU BPR). Estos productos se venden actualmente en el mercado del Reino Unido. "
            "Estos productos se fabrican de acuerdo con las normas de buenas prácticas de fabricación "
            "establecidas en las leyes del Reino Unido Los productos fueron fabricados en Alemania "
            "por Manufacturer Name en 123 MANUFACTURER, MANUFACTURETON 123456"
        )

    def test_schedule_text(self, cfs_app_submitted, exporter_one_contact):
        country = Country.objects.get(name="Germany")
        schedule = cfs_app_submitted.schedules.first()

        st = ScheduleText(schedule, country)

        assert isinstance(st.english_paragraphs, ScheduleParagraphs)
        assert st.english_paragraphs.paragraph
        assert st.translation_paragraphs is None

    def test_schedule_text_translation(self, cfs_app_submitted, exporter_one_contact):
        country = Country.objects.get(name="Argentina")
        schedule = cfs_app_submitted.schedules.first()

        st = ScheduleText(schedule, country)

        assert isinstance(st.english_paragraphs, ScheduleParagraphs)
        assert st.english_paragraphs.paragraph
        assert isinstance(st.translation_paragraphs, ScheduleParagraphs)
        assert st.translation_paragraphs.paragraph

    def test_fetch_schedule_text(self, cfs_app_submitted, exporter_one_contact):
        country = Country.objects.get(name="Argentina")

        schedule1 = CFSSchedule.objects.create(
            application=cfs_app_submitted,
            exporter_status=CFSSchedule.ExporterStatus.IS_MANUFACTURER,
            brand_name_holder=YesNoChoices.yes,
            product_eligibility=CFSSchedule.ProductEligibility.SOLD_ON_UK_MARKET,
            goods_placed_on_uk_market=YesNoChoices.yes,
            goods_export_only=YesNoChoices.no,
            country_of_manufacture=country,
            manufacturer_name="Manufacturer Name",
            manufacturer_address="123 Manufacturer, Manufactureton",
            manufacturer_postcode="123456",
            schedule_statements_is_responsible_person=True,
            schedule_statements_accordance_with_standards=True,
            created_by=exporter_one_contact,
        )

        schedule1.legislations.add(self.aerosol_pl)

        schedule2 = CFSSchedule.objects.create(
            application=cfs_app_submitted,
            exporter_status=CFSSchedule.ExporterStatus.IS_MANUFACTURER,
            brand_name_holder=YesNoChoices.yes,
            product_eligibility=CFSSchedule.ProductEligibility.MEET_UK_PRODUCT_SAFETY,
            goods_placed_on_uk_market=YesNoChoices.no,
            goods_export_only=YesNoChoices.yes,
            country_of_manufacture=country,
            manufacturer_name="Manufacturer Name",
            manufacturer_address="123 Manufacturer, Manufactureton",
            manufacturer_postcode="123456",
            schedule_statements_is_responsible_person=True,
            schedule_statements_accordance_with_standards=True,
            created_by=exporter_one_contact,
        )

        schedule2.legislations.add(self.aerosol_pl)

        cfs_app_submitted.refresh_from_db()

        result = fetch_schedule_text(cfs_app_submitted, country)

        assert schedule1.pk in result
        assert schedule2.pk in result
        assert len(result) == cfs_app_submitted.schedules.count()

    def test_no_edit_cfs_schedule_template(self):
        cfs_schedule_template = Template.objects.get(template_type=Template.CFS_SCHEDULE)
        assert not EditTemplate().display(cfs_schedule_template)
