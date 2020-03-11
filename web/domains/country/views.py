import structlog as logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic.list import ListView

from web.auth.mixins import RequireRegisteredMixin
from web.views import ModelCreateView, ModelDetailView, ModelUpdateView
from web.views.mixins import PageTitleMixin, PostActionMixin

from .forms import (CountryCreateForm, CountryEditForm, CountryGroupEditForm,
                    CountryNameFilter, CountryTranslationEditForm,
                    CountryTranslationSetEditForm)
from .models import (Country, CountryGroup, CountryTranslation,
                     CountryTranslationSet)

logger = logging.getLogger(__name__)


class CountryListView(RequireRegisteredMixin, ListView):
    model = Country
    template_name = 'web/country/list.html'
    filterset_class = CountryNameFilter
    permission_required = \
        'web.COUNTRY_SUPER_USERS:COUNTRY_SET_SUPER_USER:COUNTRY_MANAGE'


class CountryEditView(ModelUpdateView):
    model = Country
    template_name = 'web/country/edit.html'
    form_class = CountryEditForm
    success_url = reverse_lazy('country-list')
    cancel_url = success_url
    permission_required = \
        'web.COUNTRY_SUPER_USERS:COUNTRY_SET_SUPER_USER:COUNTRY_MANAGE'

    def get_page_title(self):
        return f"Editing '{self.object.name}'"


class CountryCreateView(ModelCreateView):
    model = Country
    template_name = 'web/country/edit.html'
    form_class = CountryCreateForm
    success_url = reverse_lazy('country-list')
    cancel_url = success_url
    page_title = 'New Country'
    permission_required = \
        'web.COUNTRY_SUPER_USERS:COUNTRY_SET_SUPER_USER:COUNTRY_MANAGE'


def search_countries(request, selected_countries):
    """
    Renders countries list with a name filter. Can be used with
    any views. Used to serve the country search page from any url.

    selected lists countries already in use. seleected list will be excluded
    from search results and displayed sepearates

    e.g. country group

    """
    context = {
        'filter':
        CountryNameFilter(request.POST or {}, queryset=Country.objects.all()),
        'selected_countries':
        selected_countries
    }
    return render(request, 'web/country/search.html', context)


class CountryGroupView(ModelDetailView):
    model = CountryGroup
    template_name = 'web/country/groups/view.html'
    form_class = CountryGroupEditForm
    permission_required = \
        'web.COUNTRY_SUPER_USERS:COUNTRY_SET_SUPER_USER:COUNTRY_GROUP_MANAGE'

    def get_object(self):
        pk = self.kwargs.get(self.pk_url_kwarg)
        if pk:
            return CountryGroup.objects.filter(pk=pk).get()

        return CountryGroup.objects.first()

    def get_context_data(self, object):
        context = super().get_context_data(object)
        context['groups'] = CountryGroup.objects.all()
        return context

    def get_page_title(self):
        return f"Viewing '{self.object.name}'"


class CountryGroupEditView(PostActionMixin, ModelUpdateView):
    model = CountryGroup
    template_name = 'web/country/groups/edit.html'
    form_class = CountryGroupEditForm
    permission_required = \
        'web.COUNTRY_SUPER_USERS:COUNTRY_SET_SUPER_USER:COUNTRY_GROUP_MANAGE'

    def get_object(self):
        pk = self.kwargs.get(self.pk_url_kwarg)
        if pk:
            return CountryGroup.objects.filter(pk=pk).get()
        return CountryGroup.objects.first()

    def _get_posted_countries(self):
        countries = self.request.POST.getlist('countries')
        return Country.objects.filter(pk__in=countries)

    def _get_countries(self):
        request = self.request
        if not request.POST:  # First request
            if self.object.id:
                return self.object.countries.all()
            else:
                return Country.objects.none()
        elif request.POST.get('action') == 'accept_countries':
            country_selection = request.POST.getlist('country-selection')
            return Country.objects.filter(pk__in=country_selection)
        else:
            return self._get_posted_countries()

    def get_context_data(self):
        context = super().get_context_data()
        context.update({
            'groups': CountryGroup.objects.all(),
            'countries': self._get_countries(),
            'form': self.form
        })
        return context

    def _render(self):
        self.object = self.get_object()
        return super().render_to_response(self.get_context_data())

    def add_country(self, request, pk=None):
        countries = self._get_countries()
        return search_countries(request, countries)

    def filter_countries(self, request, pk=None):
        countries = self._get_posted_countries()
        return search_countries(request, countries)

    def accept_countries(self, request, pk=None):
        self.form = CountryGroupEditForm(instance=self.get_object())
        return self._render()

    def get(self, request, pk=None):
        self.form = CountryGroupEditForm(instance=self.get_object())
        return self._render()

    def get_page_title(self):
        return f"Editing '{self.object.name}'"

    @transaction.atomic
    def save(self, request, pk=None):
        form = CountryGroupEditForm(request.POST, instance=self.get_object())
        if form.is_valid():
            country_group = form.save()
            countries = request.POST.getlist('countries')
            country_group.countries.set(countries)
            return redirect(
                reverse('country-group-view', args=[country_group.id]))

        self.form = form
        return self._render()


class CountryGroupCreateView(CountryGroupEditView):
    permission_required = \
        'web.COUNTRY_SUPER_USERS:COUNTRY_SET_SUPER_USER:COUNTRY_GROUP_CREATE'

    def get_object(self):
        return CountryGroup()

    def get_page_title(self):
        return 'New Country Group'


class CountryTranslationSetListView(PageTitleMixin, PostActionMixin, ListView):
    model = CountryTranslationSet
    template_name = 'web/country/translations/list.html'
    page_title = 'Manage Country Translation Sets'
    permission_required = \
        'web.COUNTRY_SUPER_USERS:COUNTRY_SET_SUPER_USER:COUNTRY_MANAGE'

    def get_form(self, request):
        action = self.request.POST.get('action', None)
        if action == 'save':
            return CountryTranslationSetEditForm(self.request.POST)
        else:
            return CountryTranslationSetEditForm()

    def get_context_data(self):
        context = super().get_context_data()
        context['form'] = self.get_form(self.request)
        return context

    def save(self, request):
        form = self.get_form(request)
        logger.debug(form.data)
        if form.is_valid():
            instance = form.save()
            logger.debug(instance.name)
            return redirect(reverse('country-translation-set-list'))

        return super().get(request)


class CountryTranslationSetEditView(PostActionMixin, ModelUpdateView):
    model = CountryTranslationSet
    template_name = 'web/country/translations/edit.html'
    form_class = CountryTranslationSetEditForm
    success_url = 'country-translation-set-edit'
    permission_required = \
        'web.COUNTRY_SUPER_USERS:COUNTRY_SET_SUPER_USER:COUNTRY_MANAGE'

    def get(self, request, pk=None):
        set = super().get_object()
        if not set.is_active:
            return redirect(reverse('country-translation-set-list'))

        return super().get(request)

    def get_missing_translations(self, country_list, country_translations):
        missing_translations = []
        remaining_count = 0
        for country in country_list:
            if country.id not in country_translations:
                if len(missing_translations) < 6:
                    missing_translations.append(country)
                else:
                    remaining_count += 1

        return {
            'countries': missing_translations,
            'remaining': remaining_count
        }

    def get_context_data(self):
        context = super().get_context_data()
        country_list = Country.objects.filter(is_active=True).all()
        country_translations = CountryTranslation.objects.filter(
            translation_set=self.object).all()
        translations = {}
        for translation in country_translations:
            translations[translation.country.id] = translation.translation

        context.update({
            'translations':
            translations,
            'country_list':
            country_list,
            'missing_translations':
            self.get_missing_translations(country_list, country_translations)
        })
        return context

    def get_success_url(self):
        object = super().get_object()
        return reverse(self.success_url, args=[object.id])

    def get_page_title(self):
        return f"Editing '{self.object.name}'"

    def archive(self, request, pk=None):
        super().archive(request)
        return redirect(reverse('country-translation-set-list'))


class CountryTranslationCreateUpdateView(ModelUpdateView):
    model = CountryTranslation
    template_name = 'web/country/translations/translation/edit.html'
    form_class = CountryTranslationEditForm
    permission_required = \
        'web.COUNTRY_SUPER_USERS:COUNTRY_SET_SUPER_USER:COUNTRY_MANAGE'

    def get_object(self, queryset=None):
        try:
            return CountryTranslation.objects.filter(
                translation_set=self.translation_set,
                country=self.country).get()
        except ObjectDoesNotExist:
            return None

    def get_form(self):
        translation = self.get_object()
        logger.debug('Translation: %s', translation)
        return self.form_class(self.request.POST or None, instance=translation)

    def set_data(self, request, set_pk, country_pk, **kwargs):
        self.translation_set = \
            CountryTranslationSet.objects.filter(pk=set_pk).get()
        self.country = Country.objects.filter(pk=country_pk).get()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context.update({
            'translation_set': self.translation_set,
            'country': self.country
        })
        return context

    def get_success_url(self):
        return reverse('country-translation-set-edit',
                       args=[
                           self.translation_set.id,
                       ])

    def form_valid(self, form):
        form.instance.country_id = self.country.id
        form.instance.translation_set_id = self.translation_set.id
        form.save()
        return redirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        self.set_data(request, **kwargs)
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.set_data(request, **kwargs)
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)
