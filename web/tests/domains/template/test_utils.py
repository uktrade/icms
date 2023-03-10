import datetime as dt
from unittest.mock import Mock

import pytest

from web.domains.case.services import document_pack
from web.domains.country.models import Country
from web.domains.template.context import CoverLetterTemplateContext
from web.domains.template.models import Template
from web.domains.template.utils import (
    add_application_default_cover_letter,
    add_endorsements_from_application_type,
    add_template_data_on_submit,
    get_context_dict,
    get_cover_letter_content,
    get_letter_fragment,
)
from web.models import (
    DFLApplication,
    EndorsementImportApplication,
    ImportApplicationType,
    OpenIndividualLicenceApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
)
from web.utils.pdf.types import DocumentTypes


def _create_sil_app(test_import_user, importer, office, **kwargs):
    """Creates a SIL app with default data overridable with kwargs"""
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.SIL
    )

    sil_data = {
        "created_by": test_import_user,
        "last_updated_by": test_import_user,
        "importer": importer,
        "importer_office": office,
        "process_type": SILApplication.PROCESS_TYPE,
        "application_type": application_type,
        "contact": test_import_user,
        "submit_datetime": dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.timezone.utc),
    } | kwargs

    app = SILApplication.objects.create(**sil_data)

    return app


def test_add_endorsements_from_application_type(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    active_endorsements = Template.objects.filter(
        template_name__startswith="Test Endorsement", is_active=True
    )

    # Add active endorsement to application type
    application_type.endorsements.add(*active_endorsements)

    inactive_endorsement = Template.objects.filter(
        template_type=Template.ENDORSEMENT, is_active=False
    ).first()

    # Add inactive endorsement to application type
    application_type.endorsements.add(inactive_endorsement)

    app = DFLApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=application_type,
    )

    add_endorsements_from_application_type(app)

    # Check application only includes active endorsements from application type
    assert app.endorsements.count() == 2
    assert list(app.endorsements.values_list("content", flat=True).order_by("content")) == list(
        active_endorsements.values_list("template_content", flat=True).order_by("template_content")
    )


def test_add_endorsements_from_application_type_added(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    endorsements = Template.objects.filter(template_name__startswith="Test Endorsement")

    # Add active endorsements to application type
    application_type.endorsements.add(*endorsements)

    app = DFLApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=application_type,
    )

    # Add endorsement to application
    EndorsementImportApplication.objects.create(
        import_application_id=app.pk, content="Test Content"
    )
    add_endorsements_from_application_type(app)

    # Check only endorsement that was one the application is still on the application
    assert app.endorsements.count() == 1
    assert list(app.endorsements.values_list("content", flat=True)) == ["Test Content"]


def test_add_template_data_on_submit(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    active_endorsements = Template.objects.filter(
        template_name__startswith="Test Endorsement", is_active=True
    )

    # Add active endorsement to application type
    application_type.endorsements.add(*active_endorsements)

    app = DFLApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=application_type,
        submit_datetime=dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.timezone.utc),
        consignment_country=Country.objects.get(name="Germany"),
        origin_country=Country.objects.get(name="Albania"),
    )

    template = Template.objects.get(template_code="COVER_FIREARMS_DEACTIVATED_FIREARMS")

    add_template_data_on_submit(app)

    # Check application only includes active endorsements from application type
    assert app.endorsements.count() == 2
    assert list(app.endorsements.values_list("content", flat=True).order_by("content")) == list(
        active_endorsements.values_list("template_content", flat=True).order_by("template_content")
    )

    assert app.cover_letter_text == template.template_content


def test_get_cover_letter_context(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    app = DFLApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=application_type,
        contact=test_import_user,
        submit_datetime=dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.timezone.utc),
        consignment_country=Country.objects.get(name="Germany"),
        origin_country=Country.objects.get(name="Albania"),
    )

    template_text = """
    Hello [[CONTACT_NAME]], [[APPLICATION_SUBMITTED_DATE]], [[COUNTRY_OF_CONSIGNMENT]]
    [[COUNTRY_OF_ORIGIN]] [[LICENCE_NUMBER]] [[LICENCE_END_DATE]]
    """

    context = CoverLetterTemplateContext(app, DocumentTypes.COVER_LETTER_PREVIEW)
    context_dict = get_context_dict(template_text, context)

    assert context_dict["APPLICATION_SUBMITTED_DATE"] == "25 December 2022"
    assert context_dict["CONTACT_NAME"] == test_import_user.full_name
    assert context_dict["COUNTRY_OF_CONSIGNMENT"] == "Germany"
    assert context_dict["COUNTRY_OF_ORIGIN"] == "Albania"
    assert context_dict["LICENCE_NUMBER"] == '<span class="placeholder">[[LICENCE_NUMBER]]</span>'
    assert (
        context_dict["LICENCE_END_DATE"] == '<span class="placeholder">[[LICENCE_END_DATE]]</span>'
    )

    doc_pack = document_pack.pack_draft_create(app)
    doc_pack.licence_start_date = dt.date.today()
    doc_pack.licence_end_date = dt.date(dt.date.today().year + 1, 12, 1)
    doc_pack.save()
    document_pack.doc_ref_documents_create(app, lock_manager=Mock())

    context = CoverLetterTemplateContext(app, DocumentTypes.COVER_LETTER_PRE_SIGN)
    context_dict = get_context_dict(template_text, context)

    assert context_dict["APPLICATION_SUBMITTED_DATE"] == "25 December 2022"
    assert context_dict["CONTACT_NAME"] == test_import_user.full_name
    assert context_dict["COUNTRY_OF_CONSIGNMENT"] == "Germany"
    assert context_dict["COUNTRY_OF_ORIGIN"] == "Albania"
    assert context_dict["LICENCE_NUMBER"] == document_pack.doc_ref_licence_get(doc_pack).reference
    assert context_dict["LICENCE_END_DATE"] == "01 December " + str(dt.date.today().year + 1)

    context = CoverLetterTemplateContext(app, DocumentTypes.COVER_LETTER_SIGNED)
    context_dict = get_context_dict(template_text, context)

    assert context_dict["APPLICATION_SUBMITTED_DATE"] == "25 December 2022"
    assert context_dict["CONTACT_NAME"] == test_import_user.full_name
    assert context_dict["COUNTRY_OF_CONSIGNMENT"] == "Germany"
    assert context_dict["COUNTRY_OF_ORIGIN"] == "Albania"
    assert context_dict["LICENCE_NUMBER"] == document_pack.doc_ref_licence_get(doc_pack).reference
    assert context_dict["LICENCE_END_DATE"] == "01 December " + str(dt.date.today().year + 1)

    context = CoverLetterTemplateContext(app, DocumentTypes.CERTIFICATE)

    with pytest.raises(ValueError, match=r"CERTIFICATE is not a valid document type"):
        get_context_dict(template_text, context)


def test_get_cover_letter_invalid_context(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    app = DFLApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=application_type,
        contact=test_import_user,
        submit_datetime=dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.timezone.utc),
        consignment_country=Country.objects.get(name="Germany"),
        origin_country=Country.objects.get(name="Albania"),
    )

    template_text = "Hello [[INVALID]]"
    context = CoverLetterTemplateContext(app, DocumentTypes.COVER_LETTER_PREVIEW)
    with pytest.raises(
        ValueError, match=r"INVALID is not a valid cover letter template context value"
    ):
        get_context_dict(template_text, context)


def test_dfl_add_application_default_cover_letter(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    app = DFLApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=application_type,
        contact=test_import_user,
        submit_datetime=dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.timezone.utc),
    )

    template = Template.objects.get(template_code="COVER_FIREARMS_DEACTIVATED_FIREARMS")

    add_application_default_cover_letter(app)
    assert app.cover_letter_text == template.template_content


def test_get_cover_letter_content(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    app = DFLApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=application_type,
        contact=test_import_user,
        submit_datetime=dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.timezone.utc),
        consignment_country=Country.objects.get(name="Germany"),
        origin_country=Country.objects.get(name="Albania"),
        cover_letter_text=None,
    )

    content = get_cover_letter_content(app, DocumentTypes.COVER_LETTER_PREVIEW)
    assert content == ""

    app.cover_letter_text = "Hello [[CONTACT_NAME]]"
    content = get_cover_letter_content(app, DocumentTypes.COVER_LETTER_PREVIEW)
    assert content == "Hello " + str(test_import_user)


def test_oil_add_application_default_cover_letter(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.OIL
    )

    app = OpenIndividualLicenceApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=application_type,
        contact=test_import_user,
        submit_datetime=dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.timezone.utc),
    )

    template = Template.objects.get(template_code="COVER_FIREARMS_OIL")

    add_application_default_cover_letter(app)
    assert app.cover_letter_text == template.template_content


def test_sil_add_application_default_cover_letter(test_import_user, importer, office):
    app = _create_sil_app(test_import_user, importer, office)

    add_application_default_cover_letter(app)
    assert app.cover_letter_text is None


def test_sanctions_application_default_cover_letter(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.SANCTION_ADHOC
    )

    app = SanctionsAndAdhocApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=SanctionsAndAdhocApplication.PROCESS_TYPE,
        application_type=application_type,
        contact=test_import_user,
        submit_datetime=dt.datetime(2022, 12, 25, 12, 30, tzinfo=dt.timezone.utc),
    )

    with pytest.raises(
        ValueError, match=r"No default cover letter for SanctionsAndAdhocApplication"
    ):
        add_application_default_cover_letter(app)


def test_get_letter_fragment_dfl(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    app = DFLApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=application_type,
        contact=test_import_user,
    )

    with pytest.raises(ValueError, match=r"No letter fragments for process type DFLApplication"):
        get_letter_fragment(app)


@pytest.mark.parametrize(
    "mp,eu,man",
    [(None, None, None), (None, False, False), (False, None, False), (False, False, None)],
)
def test_sil_incomplete_get_letter_fragment(test_import_user, importer, office, mp, eu, man):
    app = _create_sil_app(
        test_import_user,
        importer,
        office,
        military_police=mp,
        eu_single_market=eu,
        manufactured=man,
    )

    with pytest.raises(
        ValueError, match=r"Unable to get letter fragment due to missing application data"
    ):
        get_letter_fragment(app)


@pytest.mark.parametrize(
    "mp,eu,man,tc",
    [
        (True, False, False, "FIREARMS_MARKINGS_NON_STANDARD"),
        (False, True, False, "FIREARMS_MARKINGS_NON_STANDARD"),
        (False, False, True, "FIREARMS_MARKINGS_NON_STANDARD"),
        (False, False, False, "FIREARMS_MARKINGS_STANDARD"),
    ],
)
def test_sil_get_letter_fragment(test_import_user, importer, office, mp, eu, man, tc):
    app = _create_sil_app(
        test_import_user,
        importer,
        office,
        military_police=mp,
        eu_single_market=eu,
        manufactured=man,
    )

    template = Template.objects.get(template_code=tc)
    assert get_letter_fragment(app) == template.template_content
