from django.forms import ModelForm
from django.forms.widgets import Select, Textarea
from django_filters import CharFilter, FilterSet

from .models import Country, CountryGroup, CountryTranslation, CountryTranslationSet


class CountryNameFilter(FilterSet):
    country_name = CharFilter(field_name="name", lookup_expr="icontains", label="Country Name")

    @property
    def qs(self):
        return super().qs.filter(is_active=True)

    class Meta:
        model = Country
        fields = []


class CountryGroupNameFilter(FilterSet):
    country_group_name = CharFilter(
        field_name="name", lookup_expr="icontains", label="Country Group Name"
    )

    class Meta:
        model = CountryGroup
        fields = []


class CountryCreateForm(ModelForm):
    class Meta:
        model = Country
        fields = ["name", "type", "commission_code", "hmrc_code"]
        widgets = {
            "type": Select(choices=Country.TYPES),
        }


class CountryEditForm(CountryCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"].disabled = True

    class Meta:
        model = Country
        fields = ["name", "type", "commission_code", "hmrc_code"]


class CountryGroupEditForm(ModelForm):
    class Meta:
        model = CountryGroup
        fields = ["name", "comments"]
        labels = {"name": "Group Name", "comments": "Group Comments"}
        widgets = {"comments": Textarea({"rows": 5, "cols": 20})}


class CountryTranslationSetEditForm(ModelForm):
    class Meta:
        model = CountryTranslationSet
        fields = ["name"]
        labels = {"name": "Translation Set Name"}


class CountryTranslationEditForm(ModelForm):
    class Meta:
        model = CountryTranslation
        fields = ["translation"]
