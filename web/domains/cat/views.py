from typing import TYPE_CHECKING, Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import ModelForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, View
from django_filters import FilterSet
from django_filters.views import FilterView

from web.domains.case.export.forms import form_class_for_application_type
from web.domains.cat.models import CertificateApplicationTemplate
from web.domains.user.models import User
from web.types import AuthenticatedHttpRequest

from .forms import CATFilter, CreateCATForm, EditCATForm

if TYPE_CHECKING:
    from django.db import QuerySet


class CATListView(PermissionRequiredMixin, LoginRequiredMixin, FilterView):
    template_name = "web/domains/cat/list.html"
    context_object_name = "templates"
    filterset_class = CATFilter

    def has_permission(self) -> bool:
        return _has_permission(self.request.user)

    def get_queryset(self) -> "QuerySet[CertificateApplicationTemplate]":
        return CertificateApplicationTemplate.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Certificate Application Templates"

        return context

    def get_filterset_kwargs(self, filterset_class: FilterSet) -> dict[str, Any]:
        kwargs = super().get_filterset_kwargs(filterset_class)

        if not self.request.GET:
            # Default filter of "current" templates.
            kwargs["data"] = {"is_active": True}

        return kwargs


@login_required
def create(request: AuthenticatedHttpRequest) -> HttpResponse:
    with transaction.atomic():
        if not _has_permission(request.user):
            raise PermissionDenied

        if request.POST:
            form = CreateCATForm(request.POST)
            if form.is_valid():
                cat = form.save(commit=False)
                cat.owner = request.user
                cat.save()

                messages.success(request, f"Template '{cat.name}' created.")

                return redirect(reverse("cat:list"))
        else:
            form = CreateCATForm()

        context = {
            "page_title": "Create Certificate Application Template",
            "form": form,
        }

        return render(request, "web/domains/cat/create.html", context)


@login_required
def edit(request: AuthenticatedHttpRequest, *, cat_pk: int) -> HttpResponse:
    cat = get_object_or_404(CertificateApplicationTemplate, pk=cat_pk)

    with transaction.atomic():
        if not _has_permission(request.user):
            raise PermissionDenied

        if request.POST:
            if not cat.user_can_edit(request.user):
                raise PermissionDenied

            form = EditCATForm(request.POST, instance=cat)
            if form.is_valid():
                cat = form.save()

                messages.success(request, f"Template '{cat.name}' updated.")

                return redirect(reverse("cat:list"))
        else:
            form = EditCATForm(instance=cat)

        type_ = cat.application_type
        type_display = cat.get_application_type_display()
        sidebar_links = [
            (reverse("cat:edit", kwargs={"cat_pk": cat.pk}), "Template"),
            (
                reverse("cat:edit-step", kwargs={"cat_pk": cat.pk, "step": type_.lower()}),
                f"{type_display} Application",
            ),
        ]

        context = {
            "page_title": "Edit Certificate Application Template",
            "form": form,
            "application_type": type_display,
            "sidebar_links": sidebar_links,
        }

        return render(request, "web/domains/cat/edit.html", context)


def _has_permission(user: User) -> bool:
    ilb_admin = user.has_perm("web.ilb_admin")
    exporter_user = user.has_perm("web.exporter_access")

    return ilb_admin or exporter_user


class CATEditStepView(PermissionRequiredMixin, LoginRequiredMixin, FormView):
    template_name = "web/domains/cat/edit.html"
    success_url = reverse_lazy("cat:list")

    def dispatch(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = get_object_or_404(CertificateApplicationTemplate, pk=kwargs["cat_pk"])

        if not self.object.user_can_edit(self.request.user):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def has_permission(self) -> bool:
        return _has_permission(self.request.user)

    def get_form_class(self) -> ModelForm:
        return form_class_for_application_type(self.object.application_type)

    def get_initial(self) -> dict[str, Any]:
        return self.object.form_data()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        type_ = self.object.application_type
        type_display = self.object.get_application_type_display()
        sidebar_links = [
            (reverse("cat:edit", kwargs={"cat_pk": self.object.pk}), "Template"),
            (
                reverse("cat:edit-step", kwargs={"cat_pk": self.object.pk, "step": type_.lower()}),
                f"{type_display} Application",
            ),
        ]
        kwargs = {
            "page_title": "Edit Certificate Application Template",
            "application_type": type_display,
            "sidebar_links": sidebar_links,
        }
        return super().get_context_data(**kwargs)

    def form_valid(self, form: ModelForm) -> HttpResponse:
        result = super().form_valid(form)
        # The JSON field encoder handles querysets as a list of PKs.
        self.object.data = form.cleaned_data
        self.object.save()

        messages.success(self.request, f"Template '{self.object.name}' updated.")

        return result


class CATArchiveView(PermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        cat = get_object_or_404(CertificateApplicationTemplate, pk=kwargs["cat_pk"])

        if not cat.user_can_edit(self.request.user):
            raise PermissionDenied

        cat.is_active = False
        cat.save()
        messages.success(self.request, f"Template '{cat.name}' archived.")

        return redirect("cat:list")

    def has_permission(self) -> bool:
        return _has_permission(self.request.user)


class CATRestoreView(PermissionRequiredMixin, LoginRequiredMixin, View):
    def post(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        cat = get_object_or_404(CertificateApplicationTemplate, pk=kwargs["cat_pk"])

        if not cat.user_can_edit(self.request.user):
            raise PermissionDenied

        cat.is_active = True
        cat.save()
        messages.success(self.request, f"Template '{cat.name}' restored.")

        return redirect("cat:list")

    def has_permission(self) -> bool:
        return _has_permission(self.request.user)
