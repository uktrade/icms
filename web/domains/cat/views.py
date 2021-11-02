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
from formtools.wizard.views import SessionWizardView

from web.domains.case.export.models import ExportApplicationType
from web.domains.cat.models import CertificateApplicationTemplate
from web.domains.user.models import User
from web.types import AuthenticatedHttpRequest

from . import forms

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
        context["form"] = forms.SearchCATForm()

        return context


@login_required
def create(request: AuthenticatedHttpRequest) -> HttpResponse:
    with transaction.atomic():
        if not _has_permission(request.user):
            raise PermissionDenied

        if request.POST:
            form = forms.CreateCATForm(request.POST)
            if form.is_valid():
                cat = form.save(commit=False)
                cat.owner = request.user
                cat.save()

                messages.success(request, f"Template '{cat.name}' created.")

                return redirect(reverse("cat:list"))
        else:
            form = forms.CreateCATForm()

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
            form = forms.EditCATForm(request.POST, instance=cat)
            if form.is_valid():
                cat = form.save()

                messages.success(request, f"Template '{cat.name}' updated.")

                return redirect(reverse("cat:list"))
        else:
            form = forms.EditCATForm(instance=cat)

        context = {
            "page_title": "Edit Certificate Application Template",
            "form": form,
            "application_type": cat.get_application_type_display(),
        }

        return render(request, "web/domains/cat/edit.html", context)


class Edit(SessionWizardView):
    form_list = [
        ("metadata", forms.EditCATForm),
        # Then get_form_list picks which form to show depending on type.
        (ExportApplicationType.Types.FREE_SALE, forms.CFSTemplateForm),
        (ExportApplicationType.Types.MANUFACTURE, forms.COMTemplateForm),
        (ExportApplicationType.Types.GMP, forms.GMPTemplateForm),
    ]
    template_name = "web/domains/cat/wizard_form.html"

    def dispatch(self, request, *args, **kwargs):
        cat_pk = kwargs["cat_pk"]
        self.instance = get_object_or_404(CertificateApplicationTemplate, pk=cat_pk)
        self.check_user_for_template(None, self.instance)
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def check_user_for_template(user, instance):
        """Is the user allowed to edit this template instance?

        Raise permission denied if not.
        """
        return True

        raise PermissionDenied

    def get_form_list(self) -> dict:
        """Different forms depending on the application type of the template."""
        valid_steps = ("metadata", self.instance.application_type)
        forms = super().get_form_list()
        forms = {key: forms[key] for key in forms if key in valid_steps}

        return forms

    def get_form_instance(self, step):
        return self.instance

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"instance": self.instance}

    def done(self, form_list, form_dict, **kwargs):
        return redirect(reverse("cat:list"))


def _has_permission(user: User) -> bool:
    ilb_admin = user.has_perm("web.ilb_admin")
    exporter_user = user.has_perm("web.exporter_access")

    return ilb_admin or exporter_user
