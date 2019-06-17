from django.db import transaction
from django.urls import reverse_lazy
from django_filters import CharFilter
from web.base.views import ModelListActionView, ModelEditActionView
from web.base.forms import FilterSet, ModelForm, widgets
from web.base.forms.fields import (DisplayField)
from web.base.forms.widgets import (Textarea, Display)
from web.models import Team, User
from .filters import _filter_config
from .user import search_people
from .utils import form_utils


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


class TeamListView(ModelListActionView):
    template_name = 'web/team/list.html'
    model = Team
    filter_class = TeamsFilter


class TeamEditView(ModelEditActionView):
    template_name = 'web/team/edit.html'
    form_class = TeamEditForm
    success_url = reverse_lazy('team-list')
    model = Team

    def add_member(self, request, pk):
        # save form changes to session before searching for people
        request.session['team_form'] = super().get_form(request,
                                                        pk).serialize()

        request.session['team_members'] = request.POST.getlist(
            'team_members', None)
        return search_people(request)

    def add_people(self, request, pk):
        form_data = form_utils.remove_from_session(request, 'team_form')
        selected_users = request.POST.getlist('selected_items')
        member_ids = request.session.pop('team_members')
        members = User.objects.filter(pk__in=member_ids + selected_users)
        form = super().get_form(request, pk, data=form_data)
        return super().render_response(form, {'members': members})

    def search_people(self, request, pk):
        return search_people(request)

    @transaction.atomic
    def save(self, request, pk):
        team = super().get_instance(pk)
        team.user_set.clear()
        team.user_set.add(*request.POST.getlist('team_members'))
        return super().save(request, pk)

    def get(self, request, pk):
        form = super().get_form(request, pk)
        members = form.instance.user_set.all()
        return self.render_response(
            self.get_form(request, pk), {'members': members})
