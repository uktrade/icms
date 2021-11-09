import datetime
import re
from typing import TYPE_CHECKING, Any

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.domains.case._import.fa_dfl.models import DFLApplication
from web.domains.case._import.wood.models import WoodQuotaApplication
from web.domains.commodity.models import Commodity
from web.domains.constabulary.models import Constabulary
from web.domains.country.models import Country
from web.models.shared import FirearmCommodity
from web.utils.commodity import get_active_commodities

if TYPE_CHECKING:
    from django.test.client import Client

    from web.domains.importer.models import Importer
    from web.domains.office.models import Office
    from web.domains.user.models import User


def create_in_progress_wood_app(
    importer_client: "Client", importer: "Importer", office: "Office", contact: "User"
) -> WoodQuotaApplication:
    """Creates a fully valid in progress wood application"""

    # Create the wood app
    app_pk = create_app(
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

    app_pk = create_app(
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
        "know_bought_from": False,
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
    dfl_app = DFLApplication.objects.get(pk=app_pk)

    return dfl_app


def create_app(*, client: "Client", view_name: str, importer_pk: int, office_pk: int) -> int:
    """Creates an application and returns the primary key"""

    # TODO: Extend with agent and agent_office if needed
    post_data = {"importer": importer_pk, "importer_office": office_pk}

    url = reverse(view_name)
    resp = client.post(url, post_data)

    application_pk = int(re.search(r"\d+", resp.url).group(0))

    assert resp.status_code == 302

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
    *, client: "Client", view_name: str, app_pk: int, post_data: dict[str, Any] = None
) -> None:
    """Add a document to an application."""

    url = reverse(view_name, kwargs={"application_pk": app_pk})

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

    assertRedirects(response, reverse("workbasket"), 302)
