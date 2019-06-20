from django.urls import reverse_lazy
from django_filters import CharFilter
from django.views.generic.edit import UpdateView
from web.base.forms import FilterSet, ModelForm, widgets
from web.base.forms.fields import (DisplayField)
from web.base.forms.widgets import (Textarea, Display)
from web.base.views import FilteredListView
from web.models import Team
from .filters import _filter_config
from .contacts import ContactsManagementMixin


class TeamsFilter(FilterSet):
    name = CharFilter(
        field_name='name',
        lookup_expr='icontains',
        widget=widgets.TextInput,
        label='Name')

    class Meta:
        model = Team
        fields = []
        config = _filter_config


class TeamEditForm(ModelForm):
    name = DisplayField()

    class Meta:
        model = Team
        fields = ['name', 'description']
        widgets = {
            'name': Display,
            'description': Textarea({
                'rows': 2,
                'cols': 40
            })
        }
        help_texts = {
            'name':
            "The team's name is visible to other people. You should make sure \
            that it clearly identifies this team, so it can't be confused with \
            other teams.",
            'description': "May be used to record information about the team"
        }
        config = {
            'label': {
                'cols': 'three'
            },
            'input': {
                'cols': 'six'
            },
            'padding': {
                'right': 'three'
            },
            'actions': {
                'padding': {
                    'left': None
                },
                'submit': {
                    'label': 'Save team'
                },
                'link': {
                    'label': 'Cancel changes',
                    'href': 'team-list'
                }
            }
        }


class TeamListView(FilteredListView):
    template_name = 'web/team/list.html'
    filterset_class = TeamsFilter


class TeamEditView(ContactsManagementMixin, UpdateView):
    template_name = 'web/team/edit.html'
    form_class = TeamEditForm
    success_url = reverse_lazy('team-list')
    model = Team
