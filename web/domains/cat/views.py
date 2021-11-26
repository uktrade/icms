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
            "read_only": False,
        }

        return render(request, "web/domains/cat/create.html", context)


def _has_permission(user: User) -> bool:
    ilb_admin = user.has_perm("web.ilb_admin")
    exporter_user = user.has_perm("web.exporter_access")

    return ilb_admin or exporter_user


class CATEditView(PermissionRequiredMixin, LoginRequiredMixin, FormView):
    template_name = "web/domains/cat/edit.html"
    success_url = reverse_lazy("cat:list")
    read_only = False  # Determines editing or read-only behaviour.

    def dispatch(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = get_object_or_404(CertificateApplicationTemplate, pk=kwargs["cat_pk"])

        # Different permissions if this is editing / viewing a template.
        predicate = self.object.user_can_view if self.read_only else self.object.user_can_edit
        if not predicate(self.request.user):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def has_permission(self) -> bool:
        return _has_permission(self.request.user)

    def get_form_class(self) -> ModelForm:
        if "step" in self.kwargs:
            return form_class_for_application_type(self.object.application_type)
        else:
            # This is the template's metadata form.
            return EditCATForm

    def get_form(self) -> ModelForm:
        form = super().get_form()

        if self.read_only:
            for fname in form.fields:
                form.fields[fname].disabled = True

        return form

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()

        if "step" not in self.kwargs:
            kwargs["instance"] = self.object

        return kwargs

    def get_initial(self) -> dict[str, Any]:
        if "step" in self.kwargs:
            return self.object.form_data()
        else:
            return super().get_initial()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        type_ = self.object.application_type
        type_display = self.object.get_application_type_display()

        if self.read_only:
            url_name = "view"
            page_title = "View Certificate Application Template"
        else:
            url_name = "edit"
            page_title = "Edit Certifcate Application Template"

        sidebar_links = [
            (reverse(f"cat:{url_name}", kwargs={"cat_pk": self.object.pk}), "Template"),
            (
                reverse(
                    f"cat:{url_name}-step", kwargs={"cat_pk": self.object.pk, "step": type_.lower()}
                ),
                f"{type_display} Application",
            ),
        ]
        kwargs = {
            "page_title": page_title,
            "application_type": type_display,
            "sidebar_links": sidebar_links,
            "read_only": self.read_only,
        }
        return super().get_context_data(**kwargs)

    def form_valid(self, form: ModelForm) -> HttpResponse:
        result = super().form_valid(form)

        if "step" in self.kwargs:
            # The JSON field encoder handles querysets as a list of PKs.
            self.object.data = form.cleaned_data
            self.object.save()
        else:
            # This is the metadata form for the template itself.
            form.save()

        messages.success(self.request, f"Template '{self.object.name}' updated.")

        return result


class CATReadOnlyView(CATEditView):
    read_only = True


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
