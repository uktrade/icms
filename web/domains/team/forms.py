from django.forms.fields import CharField
from django.forms.widgets import Textarea
from django_filters import CharFilter
from web.forms import ModelEditForm, ModelSearchFilter

from .models import Team


class TeamsFilter(ModelSearchFilter):
    name = CharFilter(field_name='name', lookup_expr='icontains', label='Name')

    class Meta:
        model = Team
        fields = []


class TeamEditForm(ModelEditForm):
    name = CharField()

    class Meta:
        model = Team
        fields = ['name', 'description']
        widgets = {'description': Textarea({'rows': 2, 'cols': 40})}
        help_texts = {
            'name':
            "The team's name is visible to other people. You should make sure \
            that it clearly identifies this team, so it can't be confused with \
            other teams.",
            'description': "May be used to record information about the team"
        }
