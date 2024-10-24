from web.domains.case._import.fa_sil.forms import (
    ResponsePrepSILGoodsSection582ObsoleteForm,  # /PS-IGNORE
)
from web.domains.case._import.fa_sil.forms import (
    ResponsePrepSILGoodsSection582OtherForm,  # /PS-IGNORE
)
from web.domains.case._import.fa_sil.forms import (
    SILGoodsSection582ObsoleteForm,  # /PS-IGNORE
)
from web.domains.case._import.fa_sil.forms import (
    SILGoodsSection582OtherForm,  # /PS-IGNORE
)
from web.domains.case._import.fa_sil.forms import (
    ResponsePrepSILGoodsSection1Form,
    ResponsePrepSILGoodsSection2Form,
    ResponsePrepSILGoodsSection5Form,
    SILGoodsSection1Form,
    SILGoodsSection2Form,
    SILGoodsSection5Form,
)
from web.models import ObsoleteCalibre, Section5Clause


def test_add_section1_goods_form(db):
    data = {
        "manufacture": False,
        "description": "some goods description",
        "quantity": 100,
        "unlimited_quantity": None,
    }
    form = SILGoodsSection1Form(data=data)
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] == 100
    assert form.cleaned_data["unlimited_quantity"] is False


def test_add_section1_goods_form_unlimited_quantity(db):
    data = {
        "manufacture": False,
        "description": " some\r\n goods \t description\n  ",
        "quantity": None,
        "unlimited_quantity": True,
    }
    form = SILGoodsSection1Form(data=data)
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] is None
    assert form.cleaned_data["unlimited_quantity"] is True


def test_add_section1_goods_form_manufactured_before_1900(db):
    data = {
        "manufacture": False,
        "description": "some goods description",
        "quantity": None,
        "unlimited_quantity": None,
    }
    form = SILGoodsSection1Form(data=data)
    assert form.is_valid() is False
    assert (
        form.errors["quantity"][0]
        == "You must enter either a quantity or select unlimited quantity"
    )


def test_add_section1_goods_form_unknown_quantity(db):
    data = {
        "manufacture": True,
        "description": "some goods description",
        "quantity": 100,
        "unlimited_quantity": None,
    }
    form = SILGoodsSection1Form(data=data)
    assert form.is_valid() is False


def test_add_section2_goods_form(db):
    data = {
        "manufacture": False,
        "description": "some goods description",
        "quantity": 200,
        "unlimited_quantity": None,
    }
    form = SILGoodsSection2Form(data=data)
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] == 200
    assert form.cleaned_data["unlimited_quantity"] is False


def test_add_section2_goods_form_unlimited_quantity(db):
    data = {
        "manufacture": False,
        "description": " some\r\n goods \t description\n  ",
        "quantity": None,
        "unlimited_quantity": True,
    }
    form = SILGoodsSection2Form(data=data)
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] is None
    assert form.cleaned_data["unlimited_quantity"] is True


def test_add_section2_goods_form_manufactured_before_1900(db):
    data = {
        "manufacture": False,
        "description": "some goods description",
        "quantity": None,
        "unlimited_quantity": None,
    }
    form = SILGoodsSection2Form(data=data)
    assert form.is_valid() is False
    assert (
        form.errors["quantity"][0]
        == "You must enter either a quantity or select unlimited quantity"
    )


def test_add_section5_goods_form(db):
    clause = Section5Clause.objects.filter(is_active=True).first()
    data = {
        "section_5_clause": clause,
        "manufacture": False,
        "description": "some goods description",
        "quantity": 500,
        "unlimited_quantity": None,
    }
    form = SILGoodsSection5Form(data=data)
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] == 500
    assert form.cleaned_data["unlimited_quantity"] is False


def test_add_section5_goods_form_unlimited_quantity(db):
    clause = Section5Clause.objects.filter(is_active=True).first()
    data = {
        "section_5_clause": clause,
        "manufacture": False,
        "description": " some\r\n goods \t description\n  ",
        "quantity": None,
        "unlimited_quantity": True,
    }
    form = SILGoodsSection5Form(data=data)
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] is None
    assert form.cleaned_data["unlimited_quantity"] is True


def test_add_section5_goods_form_manufactured_before_1900(db):
    clause = Section5Clause.objects.filter(is_active=True).first()
    data = {
        "section_5_clause": clause,
        "manufacture": False,
        "description": "some goods description",
        "quantity": None,
        "unlimited_quantity": None,
    }
    form = SILGoodsSection5Form(data=data)
    assert form.is_valid() is False
    assert (
        form.errors["quantity"][0]
        == "You must enter either a quantity or select unlimited quantity"
    )


def test_add_obsolete_calibre_goods_form(db):
    calibre = ObsoleteCalibre.objects.filter(is_active=True).first()
    data = {
        "curiosity_ornament": True,
        "acknowledgement": True,
        "centrefire": True,
        "manufacture": True,
        "original_chambering": True,
        "obsolete_calibre": calibre.name,
        "description": "some goods description",
        "quantity": 100,
    }

    form = SILGoodsSection582ObsoleteForm(data=data)  # /PS-IGNORE
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"


def test_add_obsolete_calibre_goods_form_clean_description(db):
    calibre = ObsoleteCalibre.objects.filter(is_active=True).first()
    data = {
        "curiosity_ornament": True,
        "acknowledgement": True,
        "centrefire": True,
        "manufacture": True,
        "original_chambering": True,
        "obsolete_calibre": calibre.name,
        "description": " some\r\n goods \t description\n  ",
        "quantity": 100,
    }

    form = SILGoodsSection582ObsoleteForm(data=data)  # /PS-IGNORE
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"


def test_add_obsolete_calibre_goods_form_errors(db):
    calibre = ObsoleteCalibre.objects.filter(is_active=True).first()
    data = {
        "curiosity_ornament": False,
        "acknowledgement": False,
        "centrefire": False,
        "manufacture": False,
        "original_chambering": False,
        "obsolete_calibre": calibre.name,
        "description": "some goods description",
        "quantity": 100,
    }

    form = SILGoodsSection582ObsoleteForm(data=data)  # /PS-IGNORE
    assert form.is_valid() is False
    assert form.errors["curiosity_ornament"][0] == (
        'If you do not intend to possess the firearm as a "curiosity or ornament" you'
        " cannot choose Section 58(2). You must change your selection to either"
        " Section 1, Section 2 or Section 5."
    )
    assert form.errors["acknowledgement"][0] == "You must acknowledge the above statement"
    assert form.errors["manufacture"][0] == (
        "If your firearm was manufactured after 1939 then you cannot choose Section 58(2)"
        " and must change your selection to either Section 1, Section 2 or Section 5."
        "<br/>If your firearm was manufactured before 1900 then an import licence is not"
        " required."
    )
    assert form.errors["centrefire"][0] == (
        "If your firearm is not a breech loading centrefire firearm, you cannot choose"
        " Section 58(2) - Obsolete Calibre. You must change your selection to either"
        " Section 1, Section 2 or Section 5."
    )
    assert form.errors["original_chambering"][0] == (
        "If your item does not retain its original chambering you cannot choose Obsolete Calibre."
    )


def test_add_section_5_other_goods_form(db):
    data = {
        "curiosity_ornament": True,
        "acknowledgement": True,
        "centrefire": True,
        "manufacture": True,
        "original_chambering": True,
        "description": "some goods description",
        "quantity": 100,
        "muzzle_loading": True,
        "rimfire": False,
        "rimfire_details": None,
        "ignition": False,
        "ignition_details": None,
        "ignition_other": None,
        "chamber": False,
        "bore": False,
        "bore_details": None,
    }

    form = SILGoodsSection582OtherForm(data=data)  # /PS-IGNORE
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"


def test_add_section_5_other_goods_form_clean_description(db):
    data = {
        "curiosity_ornament": True,
        "acknowledgement": True,
        "centrefire": True,
        "manufacture": True,
        "original_chambering": True,
        "description": " some\r\n goods \t description\n  ",
        "quantity": 100,
        "muzzle_loading": True,
        "rimfire": False,
        "rimfire_details": None,
        "ignition": False,
        "ignition_details": None,
        "ignition_other": None,
        "chamber": False,
        "bore": False,
        "bore_details": None,
    }

    form = SILGoodsSection582OtherForm(data=data)  # /PS-IGNORE
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"


def test_add_section_5_other_goods_form_errors(db):
    data = {
        "curiosity_ornament": False,
        "acknowledgement": False,
        "centrefire": False,
        "manufacture": False,
        "original_chambering": False,
        "description": "some goods description",
        "quantity": 100,
        "muzzle_loading": True,
        "rimfire": True,
        "rimfire_details": None,
        "ignition": True,
        "ignition_details": None,
        "ignition_other": None,
        "chamber": False,
        "bore": True,
        "bore_details": None,
    }

    form = SILGoodsSection582OtherForm(data=data)  # /PS-IGNORE
    assert form.is_valid() is False
    assert form.errors["curiosity_ornament"][0] == (
        'If you do not intend to possess the firearm as a "curiosity or ornament" you'
        " cannot choose Section 58(2). You must change your selection to either"
        " Section 1, Section 2 or Section 5."
    )
    assert form.errors["acknowledgement"][0] == "You must acknowledge the above statement"
    assert form.errors["manufacture"][0] == (
        "If your firearm was manufactured after 1939 then you cannot choose Section 58(2)"
        " and must change your selection to either Section 1, Section 2 or Section 5."
        "<br/>If your firearm was manufactured before 1900 then an import licence is not"
        " required."
    )
    assert (
        form.errors["bore"][0] == "Only one of the above five questions can be answered with 'Yes'"
    )
    assert form.errors["bore_details"][0] == "You must enter this item"
    assert form.errors["rimfire_details"][0] == "You must enter this item"
    assert form.errors["ignition_details"][0] == "You must enter this item"


def test_section_1_response_prep_form(db, fa_sil_app_processing):
    obj = fa_sil_app_processing.goods_section1.first()
    obj.unlimited_quantity = False
    data = {
        "description": "some goods description",
        "quantity": 100,
    }

    form = ResponsePrepSILGoodsSection1Form(instance=obj, data=data)
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] == 100


def test_section_1_response_prep_form_clean_description(db, fa_sil_app_processing):
    obj = fa_sil_app_processing.goods_section1.first()
    obj.unlimited_quantity = True
    data = {
        "description": " some\r\n goods \t description\n  ",
        "quantity": 100,
    }

    form = ResponsePrepSILGoodsSection1Form(instance=obj, data=data)
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] is None


def test_section_2_response_prep_form(db, fa_sil_app_processing):
    obj = fa_sil_app_processing.goods_section2.first()
    obj.unlimited_quantity = False
    data = {
        "description": "some goods description",
        "quantity": 200,
    }

    form = ResponsePrepSILGoodsSection2Form(instance=obj, data=data)
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] == 200


def test_section_2_response_prep_form_clean_description(db, fa_sil_app_processing):
    obj = fa_sil_app_processing.goods_section2.first()
    obj.unlimited_quantity = True
    data = {
        "description": " some\r\n goods \t description\n  ",
        "quantity": 200,
    }

    form = ResponsePrepSILGoodsSection2Form(instance=obj, data=data)
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] is None


def test_section_5_response_prep_form(db, fa_sil_app_processing):
    obj = fa_sil_app_processing.goods_section5.first()
    obj.unlimited_quantity = False
    data = {
        "description": "some goods description",
        "quantity": 500,
    }

    form = ResponsePrepSILGoodsSection5Form(instance=obj, data=data)
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] == 500


def test_section_5_response_prep_form_clean_description(db, fa_sil_app_processing):
    obj = fa_sil_app_processing.goods_section5.first()
    obj.unlimited_quantity = True
    data = {
        "description": " some\r\n goods \t description\n  ",
        "quantity": 500,
    }

    form = ResponsePrepSILGoodsSection5Form(instance=obj, data=data)
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] is None


def test_section_5_obsolete_response_prep_form(db, fa_sil_app_processing):
    obj = fa_sil_app_processing.goods_section582_obsoletes.first()  # /PS-IGNORE
    data = {
        "description": "some goods description",
        "quantity": 500,
    }

    form = ResponsePrepSILGoodsSection582ObsoleteForm(instance=obj, data=data)  # /PS-IGNORE
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] == 500


def test_section_5_obsolete_response_prep_form_clean_description(db, fa_sil_app_processing):
    obj = fa_sil_app_processing.goods_section582_obsoletes.first()  # /PS-IGNORE
    data = {
        "description": " some\r\n goods \t description\n  ",
        "quantity": 500,
    }

    form = ResponsePrepSILGoodsSection582ObsoleteForm(instance=obj, data=data)  # /PS-IGNORE
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] == 500


def test_section_5_other_response_prep_form(db, fa_sil_app_processing):
    obj = fa_sil_app_processing.goods_section582_others.first()  # /PS-IGNORE
    data = {
        "description": "some goods description",
        "quantity": 500,
    }

    form = ResponsePrepSILGoodsSection582OtherForm(instance=obj, data=data)  # /PS-IGNORE
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] == 500


def test_section_5_other_response_prep_form_clean_description(db, fa_sil_app_processing):
    obj = fa_sil_app_processing.goods_section582_others.first()  # /PS-IGNORE
    data = {
        "description": " some\r\n goods \t description\n  ",
        "quantity": 500,
    }

    form = ResponsePrepSILGoodsSection582OtherForm(instance=obj, data=data)  # /PS-IGNORE
    assert form.is_valid()
    assert form.cleaned_data["description"] == "some goods description"
    assert form.cleaned_data["quantity"] == 500
