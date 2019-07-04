from django.db.models import Count
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.urls import reverse_lazy
from web.base.forms import ModelForm, FilterSet, ReadOnlyFormMixin, widgets
from web.base.views import PostActionMixin
from web.base.views import (SecureDetailView, SecureFilteredListView,
                            SecureUpdateView, SecureCreateView)
from web.base.utils import dict_merge
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


class ObsoleteCalibreGroupDisplayForm(ReadOnlyFormMixin, ModelForm):
    class Meta(ObsoleteCalibreGroupEditForm.Meta):
        config = dict_merge(ObsoleteCalibreGroupEditForm.Meta.config, {
            'actions': None,
        })


class ObsoleteCalibreForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = ObsoleteCalibre
        fields = ['name', 'order']
        widgets = {'order': widgets.HiddenInput()}
        config = ObsoleteCalibreGroupEditForm.Meta.config


class ObsoleteCalibreFormSet(BaseInlineFormSet):

    def sorted_forms(self):
        return sorted(self.forms, key=lambda form: form.instance.order)


def new_calibres_formset(instance, queryset=None, data=None, extra=0):
    initial = None
    if extra:
        initial = [{'order': 1}]
    return inlineformset_factory(
        ObsoleteCalibreGroup,
        ObsoleteCalibre,
        form=ObsoleteCalibreForm,
        formset=ObsoleteCalibreFormSet,
        extra=extra,
        can_delete=False
        )(data,
          initial=initial,
          queryset=queryset,
          prefix='calibre',
          instance=instance)


class ObsoleteCalibreGroupBaseView(PostActionMixin):
    def get_formset(self):
        extra = 1
        queryset = None
        if self.object:
            queryset = self.object.calibres
            if not self.request.GET.get('display_archived', None):
                queryset = queryset.filter(is_active=True)
            if queryset.count() > 0:
                extra = 0

        return new_calibres_formset(
            self.object,
            queryset=queryset,
            data=self.request.POST or None,
            extra=extra)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['formset'] = self.get_formset()
        return context

    def form_valid(self, form, formset):
        order = form.instance.order
        if not order:
            last = form.instance.order = ObsoleteCalibreGroup.objects.last()
            if last:
                order = last.order
            else:
                order = 1
        form.instance.order = order
        self.object = form.save()
        formset.save()
        return super().form_valid(form=form)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = super().get_form()
        formset = self.get_formset()
        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return super().render_to_response(self.get_context_data(form=form))


class ObsoleteCalibreGroupEditView(ObsoleteCalibreGroupBaseView,
                                   SecureUpdateView):
    template_name = 'web/obsolete-calibre/group/edit.html'
    form_class = ObsoleteCalibreGroupEditForm
    model = ObsoleteCalibreGroup
    success_url = reverse_lazy('obsolete-calibre-list')


class ObsoleteCalibreGroupCreateView(ObsoleteCalibreGroupBaseView,
                                     SecureCreateView):
    template_name = 'web/obsolete-calibre/group/edit.html'
    form_class = ObsoleteCalibreGroupEditForm
    model = ObsoleteCalibreGroup
    success_url = reverse_lazy('obsolete-calibre-list')

    def get_object(self):
        return None


class ObsoleteCalibreGroupDetailView(SecureDetailView):
    template_name = 'web/obsolete-calibre/group/view.html'
    model = ObsoleteCalibreGroup

    def get_context_data(self, object):
        context = super().get_context_data()
        context['form'] = ObsoleteCalibreGroupDisplayForm(instance=object)
        if self.request.GET.get('display_archived'):
            calibres = object.calibres.all()
        else:
            calibres = object.calibres.filter(is_active=True)
        context['calibres'] = calibres
        return context


class ObsoleteCalibreListView(SecureFilteredListView):
    template_name = 'web/obsolete-calibre/group/list.html'
    filterset_class = ObsoleteCalibreGroupFilter
    model = ObsoleteCalibreGroup
    load_immediate = True
