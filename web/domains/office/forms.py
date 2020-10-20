from django import forms
from web.domains.office.models import Office


class OfficeFormSet(forms.BaseFormSet):
    def full_clean(self, *args, **kwargs):
        super().full_clean(*args, **kwargs)
        if not self.is_valid():
            return

        for form in self.forms:
            if form.instance.address is None or form.instance.address.strip() == "":
                form.add_error("address", "Cannot be empty")


class OfficeEORIForm(forms.ModelForm):
    address = forms.CharField(
        widget=forms.Textarea({"rows": 3, "required": "required"}), required=True, strip=True
    )

    class Meta:
        model = Office
        fields = ["address", "postcode", "eori_number"]


class OfficeForm(forms.ModelForm):
    address = forms.CharField(
        widget=forms.Textarea({"rows": 3, "required": "required"}), required=True, strip=True
    )

    class Meta:
        model = Office
        fields = ["address", "postcode"]
