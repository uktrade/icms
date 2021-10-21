from typing import TYPE_CHECKING, Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView

from web.domains.cat.models import CertificateApplicationTemplate
from web.domains.user.models import User
from web.types import AuthenticatedHttpRequest

from .forms import CreateCATForm, EditCATForm, SearchCATForm

if TYPE_CHECKING:
    from django.db import QuerySet


class CATListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    template_name = "web/domains/cat/list.html"
    context_object_name = "templates"

    def has_permission(self) -> bool:
        return _has_permission(self.request.user)

    def get_queryset(self) -> "QuerySet[CertificateApplicationTemplate]":
        return CertificateApplicationTemplate.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Certificate Application Templates"
        context["form"] = SearchCATForm()

        return context


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
            form = EditCATForm(request.POST, instance=cat)
            if form.is_valid():
                cat = form.save()

                messages.success(request, f"Template '{cat.name}' updated.")

                return redirect(reverse("cat:list"))
        else:
            form = EditCATForm(instance=cat)

        context = {
            "page_title": "Edit Certificate Application Template",
            "form": form,
            "application_type": cat.get_application_type_display(),
        }

        return render(request, "web/domains/cat/edit.html", context)


def _has_permission(user: User) -> bool:
    ilb_admin = user.has_perm("web.ilb_admin")
    exporter_user = user.has_perm("web.exporter_access")

    return ilb_admin or exporter_user
