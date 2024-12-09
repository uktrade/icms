from web.domains.office.forms import ImporterOfficeForm


def test_unicode_normalization():
    form = ImporterOfficeForm(
        data={
            # contain a ` (grave accent) character
            "address_1": "1234 Main St\u0060",
            "postcode": "SW1A 1AA",  # /PS-IGNORE
        }
    )
    assert form.is_valid()
    assert form.cleaned_data["address_1"] == "1234 Main St\u0027"

    form = ImporterOfficeForm(
        data={
            "address_1": "José João Caminhão Cachaçaria Pêssegó",
            "postcode": "SW1A 1AA",  # /PS-IGNORE
        }
    )
    assert form.is_valid()
    assert form.cleaned_data["address_1"] == "Jose Joao Caminhao Cachacaria Pessego"
