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

from web.models import (
    CertificateApplicationTemplate,
    CertificateOfManufactureApplicationTemplate,
    ExportApplicationType,
    User,
)
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest

from .forms import (
    CATFilter,
    CertificateOfManufactureTemplateForm,
    CreateCATForm,
    EditCATForm,
)

# TODO: Use these
# from web.models import CertificateOfFreeSaleApplicationTemplate, CertificateOfGoodManufacturingPracticeApplicationTemplate,


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

        if request.method == "POST":
            form = CreateCATForm(request.POST)
            if form.is_valid():
                cat = form.save(commit=False)
                cat.owner = request.user
                cat.save()

                match cat.application_type:
                    case ExportApplicationType.Types.FREE_SALE:
                        # TODO: Add real template
                        # TemplateCls = CertificateOfFreeSaleApplicationTemplate
                        template_cls = CertificateOfManufactureApplicationTemplate

                    case ExportApplicationType.Types.MANUFACTURE:
                        template_cls = CertificateOfManufactureApplicationTemplate

                    case ExportApplicationType.Types.GMP:
                        # TODO: Add real template
                        # TemplateCls = CertificateOfGoodManufacturingPracticeApplicationTemplate
                        template_cls = CertificateOfManufactureApplicationTemplate

                template_cls.objects.create(template=cat)
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
    exporter_admin = user.has_perm(Perms.sys.exporter_admin)
    exporter_user = user.has_perm(Perms.sys.exporter_access)

    return exporter_admin or exporter_user


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

    def get_form_class(self) -> type[ModelForm]:
        if "step" in self.kwargs:
            return form_class_for_application_type(self.object.application_type)
        else:
            # This is the template's metadata form.
            return EditCATForm

    def get_form(self, form_class=None) -> ModelForm:
        form = super().get_form(form_class)

        if self.read_only:
            for fname in form.fields:
                form.fields[fname].disabled = True

        return form

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()

        if "step" in self.kwargs:
            # TODO: Set correct instance based on step.
            # The step will change the template / related table.
            kwargs["instance"] = self.object.com_template
        else:
            kwargs["instance"] = self.object

        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs = {
            "page_title": self.get_page_title(),
            "application_type": self.object.get_application_type_display(),
            "sidebar_links": self.get_sidebar_links(),
            "read_only": self.read_only,
        }

        return super().get_context_data(**kwargs)

    def form_valid(self, form: ModelForm) -> HttpResponse:
        form.save()
        messages.success(self.request, f"Template '{self.object.name}' updated.")

        return super().form_valid(form)

    def get_page_title(self):
        action = "View" if self.read_only else "Edit"
        page_title = f"{action} Certificate Application Template"

        return page_title

    def get_sidebar_links(self):
        type_ = self.object.application_type
        url_name = "view" if self.read_only else "edit"
        type_display = self.object.get_application_type_display()

        common_steps: list[tuple[str, str]] = [
            (reverse(f"cat:{url_name}", kwargs={"cat_pk": self.object.pk}), "Template"),
            (
                reverse(
                    f"cat:{url_name}-step", kwargs={"cat_pk": self.object.pk, "step": type_.lower()}
                ),
                f"{type_display} Application",
            ),
        ]

        match self.object.application_type:
            case ExportApplicationType.Types.FREE_SALE:
                app_specific: list[tuple[str, str]] = []
            case ExportApplicationType.Types.MANUFACTURE:
                app_specific = []
            case ExportApplicationType.Types.GMP:
                app_specific = []
            case _:
                app_specific = []

        return common_steps + app_specific


def form_class_for_application_type(type_code: str) -> type[ModelForm]:
    types_forms: dict[Any, type[ModelForm]] = {
        # TODO: Use correct form
        ExportApplicationType.Types.FREE_SALE: CertificateOfManufactureTemplateForm,
        # TODO: Use correct form
        ExportApplicationType.Types.GMP: CertificateOfManufactureTemplateForm,
        ExportApplicationType.Types.MANUFACTURE: CertificateOfManufactureTemplateForm,
    }

    try:
        return types_forms[type_code]
    except KeyError:
        raise NotImplementedError(f"Type not supported: {type_code}")


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
