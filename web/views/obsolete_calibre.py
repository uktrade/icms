from django.db.models import Count
# from django.db import transaction
# from django.shortcuts import redirect, render
# from django.urls import reverse, reverse_lazy
# from django.views.generic.list import ListView
# from django.views.generic.detail import DetailView
# from django.views.generic.edit import UpdateView, CreateView
from web.base.forms import ModelForm, FilterSet, widgets
# from web.base.forms.widgets import Select, Textarea
from web.base.views import PostActionMixin, FilteredListView
# from web.base.utils import dict_merge
from web.models import ObsoleteCalibreGroup
from .filters import _filter_config
import django_filters as filter


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


class ObsoleteCalibreListView(FilteredListView):
    template_name = 'web/obsolete-calibre/group/list.html'
    filterset_class = ObsoleteCalibreGroupFilter
    load_immediate = True
