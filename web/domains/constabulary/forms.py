from django.forms.widgets import Select
from django_filters import CharFilter, ChoiceFilter
from web.forms import ModelEditForm, ModelSearchFilter

from .models import Constabulary


class ConstabulariesFilter(ModelSearchFilter):
    name = CharFilter(field_name='name',
                      lookup_expr='icontains',
                      label='Constabulary Name')

    region = ChoiceFilter(field_name='region',
                          choices=Constabulary.REGIONS,
                          lookup_expr='icontains',
                          label='Constabulary Region')

    email = CharFilter(field_name='email',
                       lookup_expr='icontains',
                       label='Email Address')

    class Meta:
        model = Constabulary
        fields = []


class ConstabularyForm(ModelEditForm):
    class Meta:
        model = Constabulary
        fields = ['name', 'region', 'email']
        labels = {
            'name': 'Constabulary Name',
            'region': 'Constabulary Region',
            'email': 'Email Address'
        }
        widgets = {'region': Select(choices=Constabulary.REGIONS)}
