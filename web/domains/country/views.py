import logging
from typing import Any, TypedDict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, FormView, ListView

from web.permissions import Perms
from web.types import AuthenticatedHttpRequest
from web.views import ModelCreateView, ModelDetailView, ModelFilterView, ModelUpdateView
from web.views.actions import Edit, ViewObject
from web.views.mixins import PageTitleMixin, PostActionMixin

from .forms import (
    CountryCreateForm,
    CountryEditForm,
    CountryGroupEditForm,
    CountryGroupNameFilter,
    CountryNameFilter,
    CountryTranslationEditForm,
    CountryTranslationSetEditForm,
)
from .models import Country, CountryGroup, CountryTranslation, CountryTranslationSet

logger = logging.getLogger(__name__)


class MissingTranslationsDict(TypedDict):
    countries: list[Country]
    remaining: int


class CountryListView(LoginRequiredMixin, PermissionRequiredMixin, PageTitleMixin, ListView):
    model = Country
    template_name = "web/domains/country/list.html"
    filterset_class = CountryNameFilter
    page_title = "Editing All Countries"
    permission_required = Perms.sys.ilb_admin

    def get_queryset(self):
        # we want to prefetch country groups for each country as it's quicker to display
        return super().get_queryset().prefetch_related("country_groups")


class CountryEditView(ModelUpdateView):
    model = Country
    template_name = "web/domains/country/edit.html"
    form_class = CountryEditForm
    success_url = reverse_lazy("country:list")
    cancel_url = success_url
    permission_required = Perms.sys.ilb_admin


class CountryCreateView(LoginRequiredMixin, PermissionRequiredMixin, PageTitleMixin, FormView):
    template_name = "web/domains/country/add.html"
    form_class = CountryCreateForm
    page_title = "Add Country"
    permission_required = Perms.sys.ilb_admin
    cancel_url = reverse_lazy("country:list")

    def form_valid(self, form: CountryCreateForm) -> HttpResponseRedirect:
        country = form.cleaned_data["name"]
        country.is_active = True
        country.save()
        return redirect(reverse_lazy("country:edit", kwargs={"pk": country.pk}))


def search_countries(request, selected_countries):
    """
    Renders countries list with a name filter. Can be used with
    any views. Used to serve the country search page from any url.

    selected lists countries already in use. seleected list will be excluded
    from search results and displayed sepearates

    e.g. country group

    """
    context = {
        "filter": CountryNameFilter(request.POST or {}, queryset=Country.objects.all()),
        "selected_countries": selected_countries,
        "page_title": "Country Search",
    }

    return TemplateResponse(request, "web/domains/country/search.html", context).render()


class EditCountryGroup(Edit):
    def href(self, obj):
        return reverse("country:group-edit", kwargs={"pk": obj.pk})


class CountryGroupListView(ModelFilterView):
    page_title = "Maintain Country Groups"
    template_name = "web/domains/country/groups/list.html"
    permission_required = Perms.sys.ilb_admin
    model = CountryGroup
    filterset_class = CountryGroupNameFilter

    class Display:
        fields = ["name"]
        fields_config = {
            "name": {"header": "Country Group Name", "method": "get_name_display"},
        }
        opts = {"inline": True, "icon_only": True}
        actions = [ViewObject(**opts), EditCountryGroup(**opts)]

    def get_initial_data(self, queryset: QuerySet) -> QuerySet:
        return queryset


class CountryGroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # PermissionRequiredMixin config
    permission_required = Perms.sys.ilb_admin

    # CreateView config
    model = CountryGroup
    fields = ("name", "comments")
    template_name = "web/domains/country/groups/add.html"

    extra_context = {"page_sub_title": "New Country Group"}


class CountryGroupView(ModelDetailView):
    model = CountryGroup
    template_name = "web/domains/country/groups/view.html"

    form_class = CountryGroupEditForm
    cancel_url = reverse_lazy("country:group-list")
    permission_required = Perms.sys.ilb_admin

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["groups"] = CountryGroup.objects.all()
        return context


class CountryGroupEditView(PostActionMixin, ModelUpdateView):
    # PostActionMixin config
    post_actions = ["add_country", "save", "accept_countries", "filter_countries"]

    # ModelUpdateView config
    model = CountryGroup
    template_name = "web/domains/country/groups/edit.html"
    form_class = CountryGroupEditForm
    permission_required = Perms.sys.ilb_admin

    def _get_posted_countries(self):
        countries = self.request.POST.getlist("countries")
        return Country.objects.filter(pk__in=countries)

    def _get_countries(self):
        request = self.request

        if not request.POST:  # First request
            return self.object.countries.all()

        elif request.POST.get("action") == "accept_countries":
            country_selection = request.POST.getlist("country-selection")
            return Country.objects.filter(pk__in=country_selection)
        else:
            return self._get_posted_countries()

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "groups": CountryGroup.objects.all(),
                "countries": self._get_countries(),
                "form": self.form,
            }
        )
        return context

    def _render(self, **kwargs: dict[str, Any]) -> HttpResponse:
        self.object = self.get_object()
        return super().render_to_response(self.get_context_data(**kwargs))

    def add_country(self, request, pk=None):
        countries = self._get_countries()
        return search_countries(request, countries)

    def filter_countries(self, request, pk=None):
        countries = self._get_posted_countries()
        return search_countries(request, countries)

    def accept_countries(
        self, request: AuthenticatedHttpRequest, **kwargs: dict[str, Any]
    ) -> HttpResponse:
        self.form = CountryGroupEditForm(instance=self.get_object())
        return self._render(**kwargs)

    def get(self, request: AuthenticatedHttpRequest, **kwargs: dict[str, Any]) -> HttpResponse:
        self.form = CountryGroupEditForm(instance=self.get_object())
        return self._render()

    def get_cancel_url(self):
        return self.get_success_url()

    @transaction.atomic
    def save(self, request, pk=None):
        form = CountryGroupEditForm(request.POST, instance=self.get_object())
        if form.is_valid():
            country_group = form.save()
            countries = request.POST.getlist("countries")
            country_group.countries.set(countries)
            return redirect(reverse("country:group-view", kwargs={"pk": country_group.id}))

        self.form = form
        return self._render()


class CountryTranslationSetListView(PostActionMixin, ModelCreateView):
    # PostActionMixin config
    post_actions = ["archive", "unarchive"]

    # ModelCreateView config
    model = CountryTranslationSet
    form_class = CountryTranslationSetEditForm
    template_name = "web/domains/country/translations/list.html"
    page_title = "Manage Country Translation Sets"
    permission_required = Perms.sys.ilb_admin

    def get_success_url(self) -> str:
        return reverse("country:translation-set-edit", kwargs={"pk": self.object.pk})

    def archive(self, request):
        translation_set = CountryTranslationSet.objects.get(pk=request.POST.get("item"))
        translation_set.is_active = False
        translation_set.save()

        messages.success(request, "Record archived successfully")
        return super().get(request)

    def unarchive(self, request):
        translation_set = CountryTranslationSet.objects.get(pk=request.POST.get("item"))
        translation_set.is_active = True
        translation_set.save()

        messages.success(request, "Record restored successfully")
        return super().get(request)

    def get_form(self):
        post = self.request.POST

        if (not post) or post.get("action"):
            return CountryTranslationSetEditForm()

        return CountryTranslationSetEditForm(post)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = CountryTranslationSet.objects.all()
        return context


class CountryTranslationSetEditView(PostActionMixin, ModelUpdateView):
    # PostActionMixin config
    post_actions = ["archive"]

    # ModelCreateView config
    model = CountryTranslationSet
    template_name = "web/domains/country/translations/edit.html"
    form_class = CountryTranslationSetEditForm
    success_url = "country:translation-set-edit"
    permission_required = Perms.sys.ilb_admin

    def get(self, request, pk=None):
        set = super().get_object()
        if not set.is_active:
            return redirect(reverse("country:translation-set-list"))

        return super().get(request)

    def get_missing_translations(
        self, country_list: QuerySet[Country], country_translations: dict[int, str]
    ) -> MissingTranslationsDict:
        missing_translations: list[Country] = []
        remaining_count = 0
        for country in country_list:
            if country.id not in country_translations:
                if len(missing_translations) < 6:
                    missing_translations.append(country)
                else:
                    remaining_count += 1

        return MissingTranslationsDict(countries=missing_translations, remaining=remaining_count)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        country_list = Country.objects.filter(is_active=True).all()
        country_translations = CountryTranslation.objects.filter(translation_set=self.object).all()
        translations = {}
        for translation in country_translations:
            translations[translation.country.id] = translation.translation

        context.update(
            {
                "translations": translations,
                "country_list": country_list,
                "missing_translations": self.get_missing_translations(country_list, translations),
            }
        )
        return context

    def get_success_url(self) -> str:
        object = super().get_object()
        return reverse(self.success_url, args=[object.id])

    def get_page_title(self):
        return f"Editing {self.object.name} Translation Set"

    def archive(self, request, pk):
        obj: CountryTranslationSet = super().get_object()
        obj.is_active = False
        obj.save()

        return redirect(reverse("country:translation-set-list"))


class CountryTranslationCreateUpdateView(ModelUpdateView):
    model = CountryTranslation
    template_name = "web/domains/country/translations/translation/edit.html"
    form_class = CountryTranslationEditForm
    permission_required = Perms.sys.ilb_admin

    def get_object(self, queryset=None):
        try:
            return CountryTranslation.objects.filter(
                translation_set=self.translation_set, country=self.country
            ).get()
        except ObjectDoesNotExist:
            return None

    def get_form(self):
        translation = self.get_object()
        logger.debug("Translation: %s", translation)
        return self.form_class(self.request.POST or None, instance=translation)

    def set_data(self, request, set_pk, country_pk, **kwargs):
        self.translation_set = CountryTranslationSet.objects.filter(pk=set_pk).get()
        self.country = Country.objects.filter(pk=country_pk).get()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"translation_set": self.translation_set, "country": self.country})
        return context

    def get_success_url(self) -> str:
        return reverse("country:translation-set-edit", args=[self.translation_set.id])

    def get_cancel_url(self):
        return self.get_success_url()

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

    def get_page_title(self):
        return f"Editing {self.translation_set.name} translation of {self.country.name}"
