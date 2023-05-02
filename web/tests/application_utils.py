import datetime
import re
from typing import TYPE_CHECKING, Any

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.models import (
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    Commodity,
    Constabulary,
    Country,
    DFLApplication,
    ExportApplicationType,
    GMPBrand,
    OpenIndividualLicenceApplication,
    SILApplication,
    WoodQuotaApplication,
)
from web.models.shared import FirearmCommodity
from web.utils.commodity import get_active_commodities

if TYPE_CHECKING:
    from django.test.client import Client

    from web.models import Exporter, Importer, Office, User


def create_in_progress_wood_app(
    importer_client: "Client", importer: "Importer", office: "Office", contact: "User"
) -> WoodQuotaApplication:
    """Creates a fully valid in progress wood application"""

    # Create the wood app
    app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-wood-quota",
        importer_pk=importer.pk,
        office_pk=office.pk,
    )

    # Save a valid set of data.
    wood_commodities = get_active_commodities(Commodity.objects.filter(commodity_type__type="Wood"))
    form_data = {
        "contact": contact.pk,
        "applicant_reference": "Wood App Reference",
        "shipping_year": datetime.date.today().year,
        "exporter_name": "Some Exporter",
        "exporter_address": "Some Exporter Address",
        "exporter_vat_nr": "123456789",
        "commodity": wood_commodities.first().pk,
        "goods_description": "Very Woody",
        "goods_qty": 43,
        "goods_unit": "cubic metres",
        "additional_comments": "Nothing more to say",
    }
    save_app_data(
        client=importer_client, view_name="import:wood:edit", app_pk=app_pk, form_data=form_data
    )

    # Add a contract file to the wood app
    add_app_file(
        client=importer_client,
        view_name="import:wood:add-contract-document",
        app_pk=app_pk,
        post_data={"reference": "reference field", "contract_date": "09-Nov-2021"},
    )
    wood_app = WoodQuotaApplication.objects.get(pk=app_pk)

    return wood_app


def create_in_progress_fa_dfl_app(
    importer_client: "Client", importer: "Importer", office: "Office", importer_contact: "User"
) -> DFLApplication:
    """Creates a fully valid in progress fa dfl application"""

    app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-fa-dfl",
        importer_pk=importer.pk,
        office_pk=office.pk,
    )

    # Save a valid set of data.
    dfl_countries = Country.objects.filter(
        country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries"
    )
    origin_country = dfl_countries[0]
    consignment_country = dfl_countries[1]
    constabulary = Constabulary.objects.first()
    form_data = {
        "contact": importer_contact.pk,
        "applicant_reference": "applicant_reference value",
        "deactivated_firearm": True,
        "proof_checked": True,
        "origin_country": origin_country.pk,
        "consignment_country": consignment_country.pk,
        "commodity_code": FirearmCommodity.EX_CHAPTER_93.value,
        "constabulary": constabulary.pk,
    }
    save_app_data(
        client=importer_client, view_name="import:fa-dfl:edit", app_pk=app_pk, form_data=form_data
    )
    issuing_country = Country.objects.filter(
        country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries"
    ).first()

    # Add a goods file to the fa-dfl app
    post_data = {
        "goods_description": "goods_description value",
        "deactivated_certificate_reference": "deactivated_certificate_reference value",
        "issuing_country": issuing_country.pk,
    }
    add_app_file(
        client=importer_client,
        view_name="import:fa-dfl:add-goods",
        app_pk=app_pk,
        post_data=post_data,
    )

    # Set the know_bought_from value
    form_data = {"know_bought_from": False}
    importer_client.post(
        reverse("import:fa:manage-import-contacts", kwargs={"application_pk": app_pk}), form_data
    )

    dfl_app = DFLApplication.objects.get(pk=app_pk)

    return dfl_app


def create_in_progress_fa_oil_app(
    importer_client: "Client", importer: "Importer", office: "Office", importer_contact: "User"
) -> OpenIndividualLicenceApplication:
    app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-fa-oil",
        importer_pk=importer.pk,
        office_pk=office.pk,
    )
    any_country = Country.objects.get(name="Any Country", is_active=True)

    form_data = {
        "contact": importer_contact.pk,
        "applicant_reference": "applicant_reference value",
        "section1": True,
        "section2": True,
        "origin_country": any_country.pk,
        "consignment_country": any_country.pk,
        "commodity_code": "ex Chapter 93",
        "know_bought_from": False,
    }
    save_app_data(
        client=importer_client, view_name="import:fa-oil:edit", app_pk=app_pk, form_data=form_data
    )

    post_data = {
        "reference": "Certificate Reference Value",
        "certificate_type": "registered",
        "constabulary": Constabulary.objects.first().pk,
        "date_issued": datetime.date.today().strftime("%d-%b-%Y"),
        "expiry_date": datetime.date.today().strftime("%d-%b-%Y"),
    }

    add_app_file(
        client=importer_client,
        view_name="import:fa:create-certificate",
        app_pk=app_pk,
        post_data=post_data,
    )

    # Set the know_bought_from value
    form_data = {"know_bought_from": False}
    importer_client.post(
        reverse("import:fa:manage-import-contacts", kwargs={"application_pk": app_pk}), form_data
    )

    oil_app = OpenIndividualLicenceApplication.objects.get(pk=app_pk)

    return oil_app


def create_in_progress_fa_sil_app(
    importer_client: "Client", importer: "Importer", office: "Office", importer_contact: "User"
) -> SILApplication:
    app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-fa-sil",
        importer_pk=importer.pk,
        office_pk=office.pk,
    )
    # Save a valid set of data.
    origin_country = Country.objects.filter(
        country_groups__name="Firearms and Ammunition (SIL) COCs"
    ).first()
    consignment_country = Country.objects.filter(
        country_groups__name="Firearms and Ammunition (SIL) COOs"
    ).first()

    form_data = {
        "contact": importer_contact.pk,
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
        "date_issued": datetime.date.today().strftime("%d-%b-%Y"),
        "expiry_date": datetime.date.today().strftime("%d-%b-%Y"),
    }

    add_app_file(
        client=importer_client,
        view_name="import:fa:create-certificate",
        app_pk=app_pk,
        post_data=post_data,
    )

    sil_app = SILApplication.objects.get(pk=app_pk)

    sil_app.goods_section1.create(manufacture=False, description="Section 1 goods", quantity=111)
    sil_app.goods_section2.create(manufacture=False, description="Section 2 goods", quantity=222)
    sil_app.goods_section5.create(
        manufacture=False,
        description="Section 5 goods",
        quantity=333,
        subsection="section 5 subsection",
    )
    sil_app.goods_section582_obsoletes.create(
        manufacture=False,
        description="Section 58 obsoletes goods",
        quantity=444,
        obsolete_calibre="Obsolete calibre value",
    )
    sil_app.goods_section582_others.create(
        manufacture=False, description="Section 58 other goods", quantity=555
    )

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


def create_in_progress_com_app(
    exporter_client: "Client", exporter: "Exporter", office: "Office", exporter_contact: "User"
) -> CertificateOfManufactureApplication:
    app_pk = create_export_app(
        client=exporter_client,
        type_code=ExportApplicationType.Types.MANUFACTURE.value,
        exporter_pk=exporter.pk,
        office_pk=office.pk,
    )

    form_data = {
        "contact": exporter_contact.pk,
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
    exporter_client: "Client", exporter: "Exporter", office: "Office", exporter_contact: "User"
) -> CertificateOfGoodManufacturingPracticeApplication:
    app_pk = create_export_app(
        client=exporter_client,
        type_code=ExportApplicationType.Types.GMP.value,
        exporter_pk=exporter.pk,
        office_pk=office.pk,
    )

    form_data = {
        "contact": exporter_contact.pk,
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
    GMPBrand.objects.create(application=gmp_app, brand_name="A Brand")

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


def create_import_app(*, client: "Client", view_name: str, importer_pk: int, office_pk: int) -> int:
    """Creates an application and returns the primary key"""

    # TODO: Extend with agent and agent_office if needed
    post_data = {"importer": importer_pk, "importer_office": office_pk}

    url = reverse(view_name)
    resp = client.post(url, post_data)

    application_pk = int(re.search(r"\d+", resp.url).group(0))

    assert resp.status_code == 302

    return application_pk


def create_export_app(*, client: "Client", type_code: str, exporter_pk: int, office_pk: int) -> int:
    url = reverse("export:create-application", kwargs={"type_code": type_code.lower()})

    post_data = {"exporter": exporter_pk, "exporter_office": office_pk}
    response = client.post(url, post_data)

    application_pk = int(re.search(r"\d+", response.url).group(0))

    assert response.status_code == 302

    return application_pk


def save_app_data(
    *, client: "Client", view_name: str, app_pk: int, form_data: dict[str, Any]
) -> None:
    """Check the form submits and redirects back to the same view."""

    view_kwargs = {"application_pk": app_pk}
    edit_url = reverse(view_name, kwargs=view_kwargs)

    response = client.post(edit_url, form_data)

    assertRedirects(response, edit_url, 302)


def add_app_file(
    *,
    client: "Client",
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


def submit_app(*, client: "Client", view_name: str, app_pk: int) -> None:
    """Submits an application."""

    view_kwargs = {"application_pk": app_pk}
    submit_url = reverse(view_name, kwargs=view_kwargs)

    form_data = {"confirmation": "I AGREE"}
    response = client.post(submit_url, form_data)

    if response.status_code == 200:
        print(response.context["errors"])

    assertRedirects(response, reverse("workbasket"), 302)
