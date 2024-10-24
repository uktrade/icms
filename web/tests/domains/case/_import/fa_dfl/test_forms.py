from django.core.files.uploadedfile import SimpleUploadedFile

from web.domains.case._import.fa_dfl.forms import (
    AddDFLGoodsCertificateForm,
    EditDFLGoodsCertificateDescriptionForm,
    EditDFLGoodsCertificateForm,
)
from web.models import Country


def test_add_goods_form(db):
    country = Country.app.get_fa_dfl_issuing_countries().first()
    document = SimpleUploadedFile("myimage.png", b"file_content")
    data = {
        "goods_description": "some goods description",
        "deactivated_certificate_reference": "1234",
        "issuing_country": country,
    }
    form = AddDFLGoodsCertificateForm(data=data, files={"document": document})
    assert form.is_valid()
    assert form.cleaned_data["goods_description"] == "some goods description"
    assert form.cleaned_data["deactivated_certificate_reference"] == "1234"


def test_add_goods_form_clean_goods_description(db):
    country = Country.app.get_fa_dfl_issuing_countries().first()
    document = SimpleUploadedFile("myimage.png", b"file_content")
    data = {
        "goods_description": " some\r\n goods \t description\n  ",
        "deactivated_certificate_reference": "1234",
        "issuing_country": country,
        "document": document,
    }
    form = AddDFLGoodsCertificateForm(data=data, files={"document": document})
    assert form.is_valid()
    assert form.cleaned_data["goods_description"] == "some goods description"
    assert form.cleaned_data["deactivated_certificate_reference"] == "1234"


def test_edit_dfl_goods_form(fa_dfl_agent_app_in_progress):
    goods = fa_dfl_agent_app_in_progress.goods_certificates.first()
    country = Country.app.get_fa_dfl_issuing_countries().first()
    data = {
        "goods_description": "some goods description",
        "deactivated_certificate_reference": "1234",
        "issuing_country": country,
    }
    form = EditDFLGoodsCertificateForm(instance=goods, data=data)
    assert form.is_valid()
    assert form.cleaned_data["goods_description"] == "some goods description"
    assert form.cleaned_data["deactivated_certificate_reference"] == "1234"


def test_edit_dfl_goods_form_clean_goods_description(fa_dfl_agent_app_in_progress):
    goods = fa_dfl_agent_app_in_progress.goods_certificates.first()
    country = Country.app.get_fa_dfl_issuing_countries().first()
    data = {
        "goods_description": " some\r\n goods \t description\n  ",
        "deactivated_certificate_reference": "1234",
        "issuing_country": country,
    }
    form = EditDFLGoodsCertificateForm(instance=goods, data=data)
    assert form.is_valid()
    assert form.cleaned_data["goods_description"] == "some goods description"
    assert form.cleaned_data["deactivated_certificate_reference"] == "1234"


def test_edit_dfl_goods_description_form(fa_dfl_agent_app_submitted):
    goods = fa_dfl_agent_app_submitted.goods_certificates.first()
    data = {"goods_description": "some goods description"}
    form = EditDFLGoodsCertificateDescriptionForm(instance=goods, data=data)
    assert form.is_valid()
    assert form.cleaned_data["goods_description"] == "some goods description"


def test_edit_dfl_goods_description_form_clean_description(fa_dfl_agent_app_submitted):
    goods = fa_dfl_agent_app_submitted.goods_certificates.first()
    data = {"goods_description": " some\r\n goods \t description\n  "}
    form = EditDFLGoodsCertificateDescriptionForm(instance=goods, data=data)
    assert form.is_valid()
    assert form.cleaned_data["goods_description"] == "some goods description"
