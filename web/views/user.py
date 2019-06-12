import django_filters as filter
from web.base.forms.forms import FilterSet
from web.base.utils import dict_merge
from .filters import _filter_config


class UserFilter(FilterSet):
    email_address = filter.CharFilter(
        field_name='personal_emails__email',
        lookup_expr='icontains',
        label='Email')
    forename = filter.CharFilter(
        field_name='first_name', lookup_expr='icontains', label='Forename')
    surname = filter.CharFilter(
        field_name='last_name', lookup_expr='icontains', label='Surname')
    organisation = filter.CharFilter(
        field_name='organisation',
        lookup_expr='icontains',
        label='Organisation')
    department = filter.CharFilter(
        field_name='department', lookup_expr='icontains', label='Department')
    job = filter.CharFilter(
        field_name='job_title', lookup_expr='icontains', label='Job')

    class Meta:
        config = dict_merge(
            _filter_config,
            {'actions': {
                'submit': {
                    'value': 'search_people'
                }
            }})
