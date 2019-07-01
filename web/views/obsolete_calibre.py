from django.db import transaction
from django.db.models import Count, Max
from django.forms import (inlineformset_factory, BaseInlineFormSet,
                          ValidationError)
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
# from django.views.generic.list import ListView
# from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, CreateView
from web.base.forms import ModelForm, FilterSet,  widgets
from web.base.forms.fields import BooleanField
from web.base.views import PostActionMixin, FilteredListView
# from web.base.utils import dict_merge
from web.models import ObsoleteCalibreGroup, ObsoleteCalibre
from .filters import _filter_config
import django_filters as filter
import logging

logger = logging.getLogger(__name__)


class ObsoleteCalibreGroupFilter(FilterSet):
    group_name = filter.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Obsolete Calibre Group Name')

    calibre_name = filter.CharFilter(
        field_name='calibres__name',
        lookup_expr='icontains',
        label='Obsolete Calibre Name')

    display_archived = filter.BooleanFilter(
        label='Display Archived',
        widget=widgets.CheckboxInput,
        method='filter_display_archived')

    def filter_display_archived(self, queryset, name, value):
        if value:
            return queryset

        # filter archived calibre groups
        return queryset.filter(is_active=True)

    @property
    def qs(self):
        self.queryset = ObsoleteCalibreGroup.objects.annotate(Count('calibres'))

        #  Filter archived querysets on first load as django_filters doesn't
        #  seem to apply filters on first load
        if not self.form.data:   # first page load
            self.queryset = self.queryset.filter(is_active=True)

        return super().qs

    class Meta:
        model = ObsoleteCalibreGroup
        fields = []
        config = _filter_config


class ObsoleteCalibreGroupEditForm(ModelForm):

    class Meta:
        model = ObsoleteCalibreGroup
        fields = ['name']
        labels = {'name': 'Group Name'}
        config = {
            'label': {
                'cols': 'three',
                'optional_indicators': False
            },
            'input': {
                'cols': 'six'
            },
            'padding': {
                'right': 'three'
            },
            'actions': {
                'padding': {
                    'left': 'three'
                },
                'link': {
                    'label': 'Cancel',
                    'href': 'obsolete-calibre-list'
                }
            }
        }


class ObsoleteCalibreForm(ModelForm):
    class Meta:
        model = ObsoleteCalibre
        fields = ['name']
        config = ObsoleteCalibreGroupEditForm.Meta.config


class ObsoleteCalibreFormSet(BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        # Don' validate unless each form is valid on its own
        if any(self.errors):
            return

        max_order = 1
        last_item = ObsoleteCalibre.objects.all().last()
        if last_item:
            max_order = last_item.order + 1
        for form in self.forms:
            if not form.instance.order:
                max_order = max_order + 1
                form.instance.order = max_order


def new_calibres_formset(instance, data=None):
    return inlineformset_factory(
        ObsoleteCalibreGroup,
        ObsoleteCalibre,
        form=ObsoleteCalibreGroupEditForm,
        formset=ObsoleteCalibreFormSet,
        extra=0,
        can_delete=True)(
            data, prefix='calibre', instance=instance)


class ObsoleteCalibreGroupEditView(PostActionMixin, UpdateView):
    template_name = 'web/obsolete-calibre/group/edit.html'
    form_class = ObsoleteCalibreGroupEditForm
    model = ObsoleteCalibreGroup
    success_url = reverse_lazy('obsolete-calibre-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['formset'] = new_calibres_formset(
            self.object,
            data=self.request.POST or None)
        return context


class ObsoleteCalibreCreateView(CreateView):
    template_name = 'web/obsolete-calibre/group/edit.html'
    form_class = ObsoleteCalibreGroupEditForm
    model = ObsoleteCalibreGroup
    success_url = reverse_lazy('obsolete-calibre-list')


class ObsoleteCalibreListView(FilteredListView):
    template_name = 'web/obsolete-calibre/group/list.html'
    filterset_class = ObsoleteCalibreGroupFilter
    model = ObsoleteCalibreGroup
    load_immediate = True
