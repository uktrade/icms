from typing import Any

from django.forms import Form, ModelChoiceField, ModelForm
from django.forms.widgets import Textarea
from django_filters import CharFilter, ChoiceFilter, FilterSet

from .models import Country, CountryGroup, CountryTranslation, CountryTranslationSet
from .types import CountryGroupName


class CountryNameFilter(FilterSet):
    country_name = CharFilter(field_name="name", lookup_expr="icontains", label="Country Name")

    @property
    def qs(self):
        return super().qs.filter(is_active=True)

    class Meta:
        model = Country
        fields: list[Any] = []


class CountryGroupNameFilter(FilterSet):
    name = ChoiceFilter(
        choices=CountryGroupName.choices,
        label="Country Group Name",
    )

    class Meta:
        model = CountryGroup
        fields: list[Any] = ["name"]


class CountryCreateForm(Form):
    name = ModelChoiceField(
        queryset=Country.objects.filter(is_active=False),
    )


class CountryEditForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"].disabled = True
        self.fields["hmrc_code"].disabled = True
        self.fields["commission_code"].disabled = True

    class Meta:
        model = Country
        fields = ["name", "type", "commission_code", "hmrc_code", "overseas_region", "is_active"]


class CountryGroupEditForm(ModelForm):
    class Meta:
        model = CountryGroup
        fields = ["name", "comments"]
        labels = {"name": "Group Name", "comments": "Group Comments"}
        widgets = {"comments": Textarea({"rows": 5, "cols": 20})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].disabled = True


class CountryTranslationSetEditForm(ModelForm):
    class Meta:
        model = CountryTranslationSet
        fields = ["name"]
        labels = {"name": "Translation Set Name"}


class CountryTranslationEditForm(ModelForm):
    class Meta:
        model = CountryTranslation
        fields = ["translation"]
