import datetime as dt
from http import HTTPStatus
from typing import Any, TypeAlias

from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import model_to_dict
from django.test.client import Client
from django.urls import resolve, reverse
from freezegun import freeze_time
from pytest_django.asserts import assertRedirects

from web.forms.fields import JQUERY_DATE_FORMAT
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    CFSSchedule,
    Commodity,
    Constabulary,
    Country,
    DFLApplication,
    ExportApplicationType,
    Exporter,
    Importer,
    NuclearMaterialApplication,
    Office,
    OpenIndividualLicenceApplication,
    ProductLegislation,
    SanctionsAndAdhocApplication,
    Section5Clause,
    SILApplication,
    Unit,
    Usage,
    User,
    WoodQuotaApplication,
)
from web.utils.commodity import get_active_commodities, get_usage_commodities

IMPORT_APPS: TypeAlias = (
    WoodQuotaApplication
    | SanctionsAndAdhocApplication
    | SILApplication
    | DFLApplication
    | OpenIndividualLicenceApplication
    | NuclearMaterialApplication
)


def create_in_progress_fa_sil_app(
    importer_client: Client,
    importer: Importer,
    office: Office,
    importer_one_contact: User,
    agent: Importer | None = None,
    agent_office: Office | None = None,
) -> SILApplication:
    app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-fa-sil",
        importer_pk=importer.pk,
        office_pk=office.pk,
        agent_pk=agent.pk if agent else None,
        agent_office_pk=agent_office.pk if agent_office else None,
    )
    # Save a valid set of data.
    origin_country = Country.app.get_fa_sil_coo_countries().first()
    consignment_country = Country.app.get_fa_sil_coc_countries().first()

    form_data = {
        "contact": importer_one_contact.pk,
        "applicant_reference": "applicant_reference value",
        "section1": True,
        "section2": True,
        "section5": True,
        "section58_obsolete": True,
        "section58_other": True,
        "military_police": True,
        "eu_single_market": True,
        "manufactured": False,
        "other_description": "other_description",
        "origin_country": origin_country.pk,
        "consignment_country": consignment_country.pk,
        "commodity_code": "ex Chapter 93",
        "know_bought_from": False,
    }
    save_app_data(
        client=importer_client, view_name="import:fa-sil:edit", app_pk=app_pk, form_data=form_data
    )

    post_data = {
        "reference": "Certificate Reference Value",
        "certificate_type": "registered",
        "constabulary": Constabulary.objects.first().pk,
        "date_issued": dt.date.today().strftime(JQUERY_DATE_FORMAT),
        "expiry_date": dt.date.today().strftime(JQUERY_DATE_FORMAT),
    }

    add_app_file(
        client=importer_client,
        view_name="import:fa:create-certificate",
        app_pk=app_pk,
        post_data=post_data,
    )

    sil_app = SILApplication.objects.get(pk=app_pk)

    # Add section 1 goods
    response = importer_client.post(
        reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": sil_app.pk, "sil_section_type": "section1"},
        ),
        {"manufacture": False, "description": "Section 1 goods", "quantity": 111},
    )

    assert response.status_code == HTTPStatus.FOUND

    # Add section 2 goods
    response = importer_client.post(
        reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": sil_app.pk, "sil_section_type": "section2"},
        ),
        {"manufacture": False, "description": "Section 2 goods", "quantity": 222},
    )

    assert response.status_code == HTTPStatus.FOUND

    # Add section 5 goods
    response = importer_client.post(
        reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": sil_app.pk, "sil_section_type": "section5"},
        ),
        {
            "manufacture": False,
            "description": "Section 5 goods",
            "quantity": 333,
            "section_5_clause": Section5Clause.objects.first().pk,
        },
    )

    assert response.status_code == HTTPStatus.FOUND

    # Add unlimited section 5 goods
    response = importer_client.post(
        reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": sil_app.pk, "sil_section_type": "section5"},
        ),
        {
            "manufacture": False,
            "description": "Unlimited Section 5 goods",
            "unlimited_quantity": True,
            "section_5_clause": Section5Clause.objects.first().pk,
        },
    )

    assert response.status_code == HTTPStatus.FOUND

    # Add section 5 obsolete calibre goods
    response = importer_client.post(
        reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": sil_app.pk, "sil_section_type": "section582-obsolete"},
        ),
        {
            "acknowledgement": True,
            "centrefire": True,
            "curiosity_ornament": True,
            "description": "Section 58 obsoletes goods",
            "manufacture": True,
            "obsolete_calibre": ".22 Extra Long Maynard",
            "original_chambering": True,
            "quantity": 444,
        },
    )

    assert response.status_code == HTTPStatus.FOUND

    # Add section 5 other goods
    response = importer_client.post(
        reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": sil_app.pk, "sil_section_type": "section582-other"},
        ),
        {
            "acknowledgement": True,
            "bore": False,
            "chamber": False,
            "curiosity_ornament": True,
            "description": "Section 58 other goods",
            "ignition": False,
            "manufacture": True,
            "muzzle_loading": True,
            "quantity": 555,
            "rimfire": False,
        },
    )

    assert response.status_code == HTTPStatus.FOUND

    add_app_file(
        client=importer_client,
        view_name="import:fa-sil:add-section5-document",
        app_pk=app_pk,
        post_data={},
    )

    # Set the know_bought_from value
    form_data = {"know_bought_from": False}
    importer_client.post(
        reverse("import:fa:manage-import-contacts", kwargs={"application_pk": app_pk}), form_data
    )

    return sil_app


def create_in_progress_sanctions_app(
    importer_client: Client,
    importer: Importer,
    office: Office,
    importer_contact: User,
    agent: Importer | None = None,
    agent_office: Office | None = None,
) -> SanctionsAndAdhocApplication:
    app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-sanctions",
        importer_pk=importer.pk,
        office_pk=office.pk,
        agent_pk=agent.pk if agent else None,
        agent_office_pk=agent_office.pk if agent_office else None,
    )
    # Save a valid set of data.
    origin_country = Country.util.get_all_countries().get(name="Belarus")
    consignment_country = Country.util.get_all_countries().first()

    form_data = {
        "contact": importer_contact.pk,
        "applicant_reference": "applicant_reference value",
        "origin_country": origin_country.pk,
        "consignment_country": consignment_country.pk,
        "exporter_name": "Test Exporter",
        "exporter_address": "Test Address",
    }

    save_app_data(
        client=importer_client,
        view_name="import:sanctions:edit",
        app_pk=app_pk,
        form_data=form_data,
    )

    sanctions_app = SanctionsAndAdhocApplication.objects.get(pk=app_pk)
    usage_records = Usage.objects.filter(
        application_type=sanctions_app.application_type,
        country=sanctions_app.origin_country,
        end_date=None,
    )
    commodities = get_usage_commodities(usage_records)

    # Add a goods to the application
    add_goods_url = reverse("import:sanctions:add-goods", kwargs={"application_pk": app_pk})

    resp = importer_client.post(
        add_goods_url,
        {
            "commodity": commodities.first().pk,
            "goods_description": "Test Goods",
            "quantity_amount": 1000,
            "value": 10500,
        },
    )
    assert resp.status_code == 302

    resp = importer_client.post(
        add_goods_url,
        {
            "commodity": commodities.last().pk,
            "goods_description": "More Commoditites",
            "quantity_amount": 56.78,
            "value": 789,
        },
    )
    assert resp.status_code == 302

    add_app_file(
        client=importer_client,
        view_name="import:sanctions:add-document",
        app_pk=app_pk,
        post_data={},
    )

    return sanctions_app


def create_in_progress_nuclear_app(
    importer_client: Client,
    importer: Importer,
    office: Office,
    importer_contact: User,
    agent: Importer | None = None,
    agent_office: Office | None = None,
) -> NuclearMaterialApplication:
    app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-nuclear",
        importer_pk=importer.pk,
        office_pk=office.pk,
        agent_pk=agent.pk if agent else None,
        agent_office_pk=agent_office.pk if agent_office else None,
    )
    # Save a valid set of data.
    origin_country = Country.util.get_all_countries().get(name="Belarus")
    consignment_country = Country.util.get_all_countries().first()

    form_data = {
        "contact": importer_contact.pk,
        "applicant_reference": "applicant_reference value",
        "origin_country": origin_country.pk,
        "consignment_country": consignment_country.pk,
        "nature_of_business": "Test nature of business",
        "consignor_name": "Test consignor name",
        "consignor_address": "Test consignor address",
        "end_user_name": "Test end user name",
        "end_user_address": "Test end user address",
        "intended_use_of_shipment": "Test intended use of shipment",
        "shipment_start_date": dt.date.today().strftime(JQUERY_DATE_FORMAT),
        "shipment_end_date": "",
        "security_team_contact_information": "Test security team contact information",
        "licence_type": NuclearMaterialApplication.LicenceType.SINGLE,
    }

    save_app_data(
        client=importer_client,
        view_name="import:nuclear:edit",
        app_pk=app_pk,
        form_data=form_data,
    )

    commodities = get_active_commodities(
        Commodity.objects.filter(commoditygroup__group_code__in=["2612", "2844"])
    )

    # Add a goods to the application
    add_goods_url = reverse("import:nuclear:add-goods", kwargs={"application_pk": app_pk})

    resp = importer_client.post(
        add_goods_url,
        {
            "commodity": commodities.first().pk,
            "goods_description": "Test Goods",
            "quantity_amount": 1000,
            "quantity_unit": Unit.objects.get(hmrc_code="23").pk,
        },
    )
    assert resp.status_code == 302

    resp = importer_client.post(
        add_goods_url,
        {
            "commodity": commodities.last().pk,
            "goods_description": "More Commoditites",
            "quantity_amount": 56.78,
            "quantity_unit": Unit.objects.get(hmrc_code="21").pk,
        },
    )
    assert resp.status_code == 302

    resp = importer_client.post(
        add_goods_url,
        {
            "commodity": commodities.all()[1].pk,
            "goods_description": "Unlimited Commoditites",
            "unlimited_quantity": True,
            "quantity_unit": Unit.objects.get(hmrc_code="23").pk,
        },
    )
    assert resp.status_code == 302

    add_app_file(
        client=importer_client,
        view_name="import:nuclear:add-document",
        app_pk=app_pk,
        post_data={},
    )

    return NuclearMaterialApplication.objects.get(pk=app_pk)


def create_in_progress_com_app(
    exporter_client: Client,
    exporter: Exporter,
    office: Office,
    exporter_one_contact: User,
    agent: Exporter | None = None,
    agent_office: Office | None = None,
) -> CertificateOfManufactureApplication:
    app_pk = create_export_app(
        client=exporter_client,
        type_code=ExportApplicationType.Types.MANUFACTURE.value,
        exporter_pk=exporter.pk,
        office_pk=office.pk,
        agent_pk=agent.pk if agent else None,
        agent_office_pk=agent_office.pk if agent_office else None,
    )

    form_data = {
        "contact": exporter_one_contact.pk,
        "countries": Country.objects.first().pk,
        "is_pesticide_on_free_sale_uk": False,
        "is_manufacturer": True,
        "product_name": "Example product name",
        "chemical_name": "Example chemical name",
        "manufacturing_process": "Example manufacturing process",
    }

    save_app_data(
        client=exporter_client, view_name="export:com-edit", app_pk=app_pk, form_data=form_data
    )

    com_app = CertificateOfManufactureApplication.objects.get(pk=app_pk)

    return com_app


def create_in_progress_gmp_app(
    exporter_client: Client,
    exporter: Exporter,
    office: Office,
    exporter_one_contact: User,
    agent: Exporter | None = None,
    agent_office: Office | None = None,
) -> CertificateOfGoodManufacturingPracticeApplication:
    app_pk = create_export_app(
        client=exporter_client,
        type_code=ExportApplicationType.Types.GMP.value,
        exporter_pk=exporter.pk,
        office_pk=office.pk,
        agent_pk=agent.pk if agent else None,
        agent_office_pk=agent_office.pk if agent_office else None,
    )

    form_data = {
        "brand_name": "A Brand",
        "contact": exporter_one_contact.pk,
        "countries": Country.objects.first().pk,
        "is_responsible_person": "yes",
        "responsible_person_name": "RP Name",
        "responsible_person_postcode": "RP Postcode",
        "responsible_person_address": "RP Address",
        "responsible_person_country": "GB",
        "is_manufacturer": "yes",
        "manufacturer_name": "MAN Name",
        "manufacturer_postcode": "MAN Postcode",
        "manufacturer_address": "MAN Address",
        "manufacturer_country": "GB",
        "gmp_certificate_issued": "ISO_22716",
        "auditor_accredited": "yes",
        "auditor_certified": "yes",
    }

    save_app_data(
        client=exporter_client, view_name="export:gmp-edit", app_pk=app_pk, form_data=form_data
    )

    gmp_app = CertificateOfGoodManufacturingPracticeApplication.objects.get(pk=app_pk)

    add_app_file(
        client=exporter_client,
        view_name="export:gmp-add-document",
        app_pk=app_pk,
        url_kwargs={"file_type": "ISO_22716"},
    )

    add_app_file(
        client=exporter_client,
        view_name="export:gmp-add-document",
        app_pk=app_pk,
        url_kwargs={"file_type": "ISO_17021"},
    )

    add_app_file(
        client=exporter_client,
        view_name="export:gmp-add-document",
        app_pk=app_pk,
        url_kwargs={"file_type": "ISO_17065"},
    )

    return gmp_app


def create_in_progress_cfs_app(
    exporter_client: Client,
    exporter: Exporter,
    office: Office,
    exporter_one_contact: User,
    agent: Exporter | None = None,
    agent_office: Office | None = None,
) -> CertificateOfFreeSaleApplication:
    app_pk = create_export_app(
        client=exporter_client,
        type_code=ExportApplicationType.Types.FREE_SALE.value,
        exporter_pk=exporter.pk,
        office_pk=office.pk,
        agent_pk=agent.pk if agent else None,
        agent_office_pk=agent_office.pk if agent_office else None,
    )

    form_data = {
        "contact": exporter_one_contact.pk,
        "countries": [Country.objects.first().pk, Country.objects.last().pk],
    }

    save_app_data(
        client=exporter_client, view_name="export:cfs-edit", app_pk=app_pk, form_data=form_data
    )

    cfs_app = CertificateOfFreeSaleApplication.objects.get(pk=app_pk)

    schedule = cfs_app.schedules.first()

    schedule_data = {
        "exporter_status": CFSSchedule.ExporterStatus.IS_MANUFACTURER,
        "brand_name_holder": "yes",
        "product_eligibility": CFSSchedule.ProductEligibility.MEET_UK_PRODUCT_SAFETY,
        "goods_placed_on_uk_market": "no",
        "goods_export_only": "yes",
        "any_raw_materials": "no",
        "country_of_manufacture": Country.app.get_cfs_com_countries().first().pk,
        "schedule_statements_accordance_with_standards": True,
        "schedule_statements_is_responsible_person": True,
        "manufacturer_name": "Man Name",
        "manufacturer_postcode": "Man Postcode",
        "manufacturer_address": "Man Address",
    }

    schedule_kwargs = {"application_pk": app_pk, "schedule_pk": schedule.pk}
    edit_schedule_url = reverse("export:cfs-schedule-edit", kwargs=schedule_kwargs)
    resp = exporter_client.post(edit_schedule_url, schedule_data)
    assert resp.status_code == 302

    # Add legislations
    schedule.refresh_from_db()
    legislation = ProductLegislation.objects.filter(is_active=True, is_biocidal=True).first()
    schedule.legislations.add(legislation)

    # Add a product to the schedule
    product = schedule.products.create(product_name="A Product")

    # Add an ingredient to the product
    product.active_ingredients.create(name="An Ingredient", cas_number="107-07-3")

    # Add product type numbers to the product
    product.product_type_numbers.create(product_type_number=1)

    return cfs_app


def create_import_app(
    *,
    client: Client,
    view_name: str,
    importer_pk: int,
    office_pk: int,
    agent_pk: int | None = None,
    agent_office_pk: int | None = None,
) -> int:
    """Creates an application and returns the primary key"""

    post_data = {
        "importer": importer_pk,
        "importer_office": office_pk,
    }

    if agent_pk and agent_office_pk:
        post_data["agent"] = agent_pk
        post_data["agent_office"] = agent_office_pk

    url = reverse(view_name)
    response = client.post(url, post_data)
    assert response.status_code == 302

    resolver = resolve(response.url)
    application_pk = resolver.kwargs["application_pk"]

    assert application_pk == resolver.kwargs.get("application_pk")

    return application_pk


def create_export_app(
    *,
    client: Client,
    type_code: str,
    exporter_pk: int,
    office_pk: int,
    agent_pk: int | None = None,
    agent_office_pk: int | None = None,
) -> int:
    url = reverse("export:create-application", kwargs={"type_code": type_code.lower()})

    post_data = {"exporter": exporter_pk, "exporter_office": office_pk}

    if agent_pk and agent_office_pk:
        post_data["agent"] = agent_pk
        post_data["agent_office"] = agent_office_pk

    response = client.post(url, post_data)
    assert response.status_code == 302

    resolver = resolve(response.url)
    application_pk = resolver.kwargs["application_pk"]

    return application_pk


def save_app_data(
    *, client: Client, view_name: str, app_pk: int, form_data: dict[str, Any]
) -> None:
    """Check the form submits and redirects back to the same view."""

    view_kwargs = {"application_pk": app_pk}
    edit_url = reverse(view_name, kwargs=view_kwargs)

    response = client.post(edit_url, form_data)

    assertRedirects(response, edit_url, 302)


def add_app_file(
    *,
    client: Client,
    view_name: str,
    app_pk: int,
    url_kwargs: dict[str, Any] | None = None,
    post_data: dict[str, Any] | None = None,
) -> None:
    """Add a document to an application."""

    url_kwargs = url_kwargs or {}
    url = reverse(view_name, kwargs={"application_pk": app_pk} | url_kwargs)

    extra = post_data or {}
    form_data = {"document": SimpleUploadedFile("myimage.png", b"file_content"), **extra}

    response = client.post(url, form_data)

    assert response.status_code == 302


def compare_import_application_with_fixture(
    app: IMPORT_APPS, app_fixture: IMPORT_APPS, app_ignore_keys: list[str]
) -> None:
    """Compare the supplied app created using real views with the supplied app_fixture.

    This ensures the app from the test and the fixture do not get out of sync.

    :param app: Application created using the test client / real endpoints
    :param app_fixture: A fixture with manually created data
    :param app_ignore_keys: names of fields that aren't suitable for comparing
    """

    expected_data = model_to_dict(app)
    fixture_data = model_to_dict(app_fixture)

    common_ignore_keys = ["id", "order_datetime", "process_ptr", "importapplication_ptr"]
    ignore_keys = common_ignore_keys + app_ignore_keys

    for k in (k for k in expected_data.keys() if k not in ignore_keys):
        expected = expected_data[k]
        fixture = fixture_data[k]

        assert (
            expected == fixture
        ), f"Key {k!r} does not match (expected: {expected!r}, ficture: {fixture!r})"


def submit_app(client: Client, view_name: str, app_pk: int) -> None:
    with freeze_time("2024-01-01 12:00:00"):
        _submit_app(client=client, view_name=view_name, app_pk=app_pk)


def resubmit_app(client: Client, view_name: str, app_pk: int) -> None:
    _submit_app(client=client, view_name=view_name, app_pk=app_pk)


def _submit_app(client: Client, view_name: str, app_pk: int) -> None:
    """Submits an application."""

    view_kwargs = {"application_pk": app_pk}
    submit_url = reverse(view_name, kwargs=view_kwargs)
    form_data = {"confirmation": "I AGREE"}
    response = client.post(submit_url, form_data)

    if response.status_code == 200:
        print(response.context["errors"])

    assertRedirects(
        response,
        reverse("survey:application_submitted", kwargs={"process_pk": app_pk}),
        302,
    )
