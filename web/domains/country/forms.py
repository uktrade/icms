from django.forms.widgets import Select, Textarea
from django_filters import CharFilter
from web.forms import ModelEditForm, ModelSearchFilter

from .models import (Country, CountryGroup, CountryTranslation,
                     CountryTranslationSet)


class CountryNameFilter(ModelSearchFilter):
    country_name = CharFilter(field_name='name',
                              lookup_expr='icontains',
                              label='Country Name')

    @property
    def qs(self):
        return super().qs.filter(is_active=True)

    class Meta:
        model = Country
        fields = []


class CountryCreateForm(ModelEditForm):
    class Meta:
        model = Country
        fields = ['name', 'type', 'commission_code', 'hmrc_code']
        widgets = {
            'type': Select(choices=Country.TYPES),
        }


class CountryEditForm(CountryCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type'].disabled = True

    class Meta:
        model = Country
        fields = ['name', 'type', 'commission_code', 'hmrc_code']


class CountryGroupEditForm(ModelEditForm):
    class Meta:
        model = CountryGroup
        fields = ['name', 'comments']
        labels = {'name': 'Group Name', 'comments': 'Group Comments'}
        widgets = {'comments': Textarea({'rows': 5, 'cols': 20})}


class CountryTranslationSetEditForm(ModelEditForm):
    class Meta:
        model = CountryTranslationSet
        fields = ['name']
        labels = {'name': 'Translation Set Name'}


class CountryTranslationEditForm(ModelEditForm):
    class Meta:
        model = CountryTranslation
        fields = ['translation']
