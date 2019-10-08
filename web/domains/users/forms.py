from django.forms.widgets import Select
from django_filters import CharFilter, ChoiceFilter
from web.forms import ModelEditForm, ModelSearchFilter

from .models import UserAccount


class UsersFilter(ModelSearchFilter):
    name = CharFilter(field_name='name',
                      lookup_expr='icontains',
                      label='Constabulary Name')

    region = ChoiceFilter(field_name='region',
                          choices=UserAccount.REGIONS,
                          lookup_expr='icontains',
                          label='Constabulary Region')

    email = CharFilter(field_name='email',
                       lookup_expr='icontains',
                       label='Email Address')

    class Meta:
        model = UserAccount
        fields = []


class UsersForm(ModelEditForm):
    class Meta:
        model = UserAccount
        fields = ['name', 'region', 'email']
        labels = {
            'name': 'Constabulary Name',
            'region': 'Constabulary Region',
            'email': 'Email Address'
        }
        widgets = {'region': Select(choices=UserAccount.REGIONS)}
