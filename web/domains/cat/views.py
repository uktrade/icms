from enum import StrEnum
from typing import TYPE_CHECKING, Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import ObjectDoesNotExist
from django.forms.models import ModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, FormView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin
from django_filters import FilterSet
from django_filters.views import FilterView

from web.domains.case.export.forms import ProductsFileUploadForm
from web.domains.case.export.utils import (
    get_product_spreadsheet_response,
    process_products_file,
)
from web.domains.case.export.views import (
    get_csf_schedule_legislation_config,
    get_show_schedule_statements_is_responsible_person,
)
from web.models import (
    CertificateApplicationTemplate,
    CertificateOfFreeSaleApplicationTemplate,
    CFSProductTemplate,
    CFSScheduleTemplate,
    ExportApplicationType,
    User,
)
from web.models.shared import AddressEntryType
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import delete_file_from_s3
from web.utils.sentry import capture_exception
from web.views.generic import InlineFormsetView

from .forms import (
    CATFilter,
    CertificateOfFreeSaleApplicationTemplateForm,
    CertificateOfGoodManufacturingPracticeApplicationTemplateForm,
    CertificateOfManufactureApplicationTemplateForm,
    CFSActiveIngredientTemplateFormSet,
    CFSManufacturerDetailsTemplateForm,
    CFSProductTemplateForm,
    CFSProductTemplateFormSet,
    CFSProductTypeTemplateFormSet,
    CFSScheduleTemplateForm,
    CreateCATForm,
    EditCATForm,
)
from .utils import (
    create_cat,
    get_user_templates,
    template_in_user_templates,
    user_can_edit_template,
)

if TYPE_CHECKING:
    from django.db import QuerySet


class CATListView(PermissionRequiredMixin, LoginRequiredMixin, FilterView):
    template_name = "web/domains/cat/list.html"
    context_object_name = "templates"
    filterset_class = CATFilter

    def has_permission(self) -> bool:
        return _has_permission(self.request.user)

    def get_queryset(self) -> "QuerySet[CertificateApplicationTemplate]":
        if self.request.GET.get("is_active") == "True":
            return get_user_templates(self.request.user)
        else:
            return get_user_templates(self.request.user, include_inactive=True)

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
                cat = create_cat(form, request.user)

                messages.success(request, f"Template '{cat.name}' created.")

                return redirect(reverse("cat:edit", kwargs={"cat_pk": cat.pk}))
        else:
            form = CreateCATForm()

        context = {
            "page_title": "Create Certificate Application Template",
            "form": form,
            "read_only": False,
            "show_template_country": form.show_template_country,
        }

        return render(request, "web/domains/cat/create.html", context)


def _has_permission(user: User) -> bool:
    exporter_admin = user.has_perm(Perms.sys.exporter_admin)
    exporter_user = user.has_perm(Perms.sys.exporter_access)

    return exporter_admin or exporter_user


class CatSteps(StrEnum):
    COM = "com"
    GMP = "gmp"
    CFS = "cfs"
    CFS_SCHEDULE = "cfs-schedule"


class CATEditView(PermissionRequiredMixin, LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = "web/domains/cat/edit.html"
    read_only = False  # Determines editing or read-only behaviour.

    def has_permission(self) -> bool:
        return _has_permission(self.request.user)

    def test_func(self):
        """Runs before dispatch - Test template permission."""
        self.object = get_object_or_404(CertificateApplicationTemplate, pk=self.kwargs["cat_pk"])

        if not template_in_user_templates(self.request.user, self.object):
            return False

        # If read_only is true then we should be able to view the template as we've already
        # checked if the template is in the user templates.
        if self.read_only:
            return True

        return user_can_edit_template(self.request.user, self.object)

    def get_page_title(self):
        action = "View" if self.read_only else "Edit"
        page_title = f"{action} Certificate Application Template"

        return page_title

    def get_template_names(self) -> list[str]:
        match self.kwargs.get("step"):
            case CatSteps.CFS:
                template = "web/domains/cat/cfs/edit.html"
            case CatSteps.CFS_SCHEDULE:
                template = "web/domains/cat/cfs/edit-schedule.html"
            case _:
                template = "web/domains/cat/edit.html"

        return [template]

    def get_success_url(self):
        url_name = "view" if self.read_only else "edit"
        step = self.kwargs.get("step")
        step_pk = self.kwargs.get("step_pk")

        match step, step_pk:
            case None, _:
                return reverse(f"cat:{url_name}", kwargs={"cat_pk": self.object.pk})

            case step, None:
                return reverse(
                    f"cat:{url_name}-step", kwargs={"cat_pk": self.object.pk, "step": step}
                )

            case step, step_pk:
                return reverse(
                    f"cat:{url_name}-step-related",
                    kwargs={
                        "cat_pk": self.object.pk,
                        "step": step,
                        "step_pk": step_pk,
                    },
                )
            case _, _:
                return reverse("cat:list")

    def form_valid(self, form: ModelForm) -> HttpResponse:
        form.save()
        messages.success(self.request, f"Template '{self.object.name}' updated.")

        return super().form_valid(form)

    def get_form(self, form_class: type[ModelForm] | None = None) -> ModelForm:
        form = super().get_form(form_class)

        if self.read_only:
            for fname in form.fields:
                form.fields[fname].disabled = True

        return form

    def get_form_class(self) -> type[ModelForm]:
        if "step" in self.kwargs:
            return form_class_for_application_type(
                self.object.application_type, self.kwargs["step"]
            )
        else:
            # This is the template's metadata form.
            return EditCATForm

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()

        if "step" in self.kwargs:
            step = self.kwargs["step"]
            match (self.object.application_type, step):
                case ExportApplicationType.Types.MANUFACTURE, CatSteps.COM:
                    instance = self.object.com_template

                case ExportApplicationType.Types.GMP, CatSteps.GMP:
                    instance = self.object.gmp_template

                case ExportApplicationType.Types.FREE_SALE, CatSteps.CFS:
                    instance = self.object.cfs_template

                case ExportApplicationType.Types.FREE_SALE, CatSteps.CFS_SCHEDULE:
                    instance = self.object.cfs_template.schedules.get(pk=self.kwargs["step_pk"])
                case _, _:
                    raise ValueError(f"Not supported: {self.object.application_type} {step}")
        else:
            instance = self.object

        kwargs["instance"] = instance

        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        app_type = self.object.application_type
        step = self.kwargs.get("step", "initial")
        form = context["form"]

        extra = {
            "page_title": self.get_page_title(),
            "application_type": self.object.application_type,
            "application_type_display": self.object.get_application_type_display(),
            "sidebar_links": self.get_sidebar_links(),
            "read_only": self.read_only,
            "step": step,
            "cat_pk": self.object.pk,
        }

        if step == "initial":
            extra["show_template_country"] = form.show_template_country

        if app_type == ExportApplicationType.Types.FREE_SALE:
            if step == CatSteps.CFS:
                extra["schedules"] = self.object.cfs_template.schedules.all().order_by("created_at")

            if step == CatSteps.CFS_SCHEDULE:
                schedule = self.object.cfs_template.schedules.get(pk=self.kwargs["step_pk"])
                extra["is_cfs_cat"] = True
                extra["schedule"] = schedule
                extra["process"] = self.object.cfs_template
                extra["legislation_config"] = get_csf_schedule_legislation_config()
                extra["show_schedule_statements_is_responsible_person"] = (
                    get_show_schedule_statements_is_responsible_person(schedule)
                )

                cfs_schedule_kwargs = {
                    "cat_pk": self.object.pk,
                    "schedule_template_pk": schedule.pk,
                }

                # Manufacturer details section context
                extra["edit_manufacturer_url"] = reverse(
                    "cat:cfs-manufacturer-update", kwargs=cfs_schedule_kwargs
                )
                extra["delete_manufacturer_url"] = reverse(
                    "cat:cfs-manufacturer-delete", kwargs=cfs_schedule_kwargs
                )

                # Products section context
                extra["is_biocidal"] = schedule.is_biocidal()
                extra["products"] = schedule.products.all().order_by("pk")
                extra["product_upload_form"] = ProductsFileUploadForm()
                extra["has_legislation"] = schedule.legislations.filter(is_active=True).exists()
                extra["upload_product_spreadsheet_url"] = reverse(
                    "cat:cfs-schedule-product-spreadsheet-upload", kwargs=cfs_schedule_kwargs
                )
                extra["download_product_spreadsheet_url"] = reverse(
                    "cat:cfs-schedule-product-download-template", kwargs=cfs_schedule_kwargs
                )
                extra["add_schedule_product_url"] = reverse(
                    "cat:cfs-schedule-product-create", kwargs=cfs_schedule_kwargs
                )
                extra["add_multiple_schedule_product_url"] = reverse(
                    "cat:cfs-schedule-product-create-multiple", kwargs=cfs_schedule_kwargs
                )

        if app_type == ExportApplicationType.Types.GMP and step == CatSteps.GMP:
            extra["include_contact"] = False
            extra["process"] = form.instance
            extra["country"] = "China"

        return context | extra

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

                template: CertificateOfFreeSaleApplicationTemplate = self.object.cfs_template
                for s_id, s in enumerate(template.schedules.all().order_by("id"), start=1):
                    app_specific.extend(self._get_schedule_links(s, s_id, url_name))

            case ExportApplicationType.Types.MANUFACTURE:
                app_specific = []
            case ExportApplicationType.Types.GMP:
                app_specific = []
            case _:
                app_specific = []

        return common_steps + app_specific

    def _get_schedule_links(
        self, schedule: CFSScheduleTemplate, num: int, url_name: str
    ) -> list[tuple[str, str]]:
        return [
            (
                reverse(
                    f"cat:{url_name}-step-related",
                    kwargs={
                        "cat_pk": self.object.pk,
                        "step": CatSteps.CFS_SCHEDULE,
                        "step_pk": schedule.pk,
                    },
                ),
                f"{url_name.title()} schedule {num}",
            ),
        ]


def form_class_for_application_type(type_code: str, step: str) -> type[ModelForm]:
    match type_code, step:
        case ExportApplicationType.Types.GMP, CatSteps.GMP:
            form_cls = CertificateOfGoodManufacturingPracticeApplicationTemplateForm

        case ExportApplicationType.Types.MANUFACTURE, CatSteps.COM:
            form_cls = CertificateOfManufactureApplicationTemplateForm

        case ExportApplicationType.Types.FREE_SALE, CatSteps.CFS:
            form_cls = CertificateOfFreeSaleApplicationTemplateForm

        case ExportApplicationType.Types.FREE_SALE, CatSteps.CFS_SCHEDULE:
            form_cls = CFSScheduleTemplateForm
        case _, _:
            raise ValueError(f"Type / Step not supported: {type_code} {step}")

    return form_cls


class CATReadOnlyView(CATEditView):
    read_only = True


class CATArchiveView(PermissionRequiredMixin, LoginRequiredMixin, View):
    def has_permission(self) -> bool:
        return _has_permission(self.request.user)

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        cat = get_object_or_404(CertificateApplicationTemplate, pk=kwargs["cat_pk"])

        user = self.request.user
        if not template_in_user_templates(user, cat) or not user_can_edit_template(user, cat):
            raise PermissionDenied

        cat.is_active = False
        cat.save()
        messages.success(self.request, f"Template '{cat.name}' archived.")

        return redirect("cat:list")


class CATRestoreView(PermissionRequiredMixin, LoginRequiredMixin, View):
    def has_permission(self) -> bool:
        return _has_permission(self.request.user)

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        cat = get_object_or_404(CertificateApplicationTemplate, pk=kwargs["cat_pk"])
        user = self.request.user
        if not template_in_user_templates(
            user, cat, include_inactive=True
        ) or not user_can_edit_template(user, cat):
            raise PermissionDenied

        cat.is_active = True
        cat.save()
        messages.success(self.request, f"Template '{cat.name}' restored.")

        return redirect("cat:list")


# Extra template views relating to the CFS Application.
class CFSTemplatePermissionRequiredMixin(PermissionRequiredMixin):
    """Permission required mixin common to all Edit CFS Template views."""

    def has_permission(self) -> bool:
        if not _has_permission(self.request.user):
            return False

        cat = get_object_or_404(CertificateApplicationTemplate, pk=self.kwargs["cat_pk"])

        user = self.request.user
        if not template_in_user_templates(user, cat) or not user_can_edit_template(user, cat):
            return False

        return True


class CFSScheduleTemplateAddView(
    SingleObjectMixin, CFSTemplatePermissionRequiredMixin, LoginRequiredMixin, View
):
    # SingleObjectMixin
    model = CertificateApplicationTemplate
    pk_url_kwarg: str = "cat_pk"

    # View
    http_method_names = ["post"]

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.get_object().cfs_template.schedules.create(created_by=self.request.user)

        return redirect(
            reverse("cat:edit-step", kwargs={"cat_pk": self.kwargs["cat_pk"], "step": CatSteps.CFS})
        )


class CFSScheduleTemplateCopyView(CFSTemplatePermissionRequiredMixin, LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        schedule_template = get_cfs_schedule_template(**kwargs)

        copy_schedule(schedule_template, self.request.user)

        return redirect(
            reverse("cat:edit-step", kwargs={"cat_pk": self.kwargs["cat_pk"], "step": CatSteps.CFS})
        )


def copy_schedule(schedule: CFSScheduleTemplate, user: User) -> None:
    """Copy a template schedule.

    How to copy a model instance:
    https://docs.djangoproject.com/en/3.2/topics/db/queries/#copying-model-instances
    """

    # ManyToMany you can just use `.all()` to get the records
    # ForeignKeys you have to fetch from the db before the save.
    legislations_to_copy = schedule.legislations.all()
    products_to_copy = [p for p in schedule.products.all().order_by("pk")]

    schedule.pk = None
    schedule._state.adding = True
    schedule.created_by = user
    schedule.save()

    # Copy the legislation records
    schedule.legislations.set(legislations_to_copy)

    # copy the product records
    for product in products_to_copy:
        product_types_to_copy = [pt for pt in product.product_type_numbers.all().order_by("pk")]
        ingredients_to_copy = [i for i in product.active_ingredients.all().order_by("pk")]

        product.pk = None
        product._state.adding = True
        product.schedule = schedule
        product.save()

        for ptn in product_types_to_copy:
            ptn.pk = None
            ptn._state.adding = True
            ptn.product = product
            ptn.save()

        for ingredient in ingredients_to_copy:
            ingredient.pk = None
            ingredient._state.adding = True
            ingredient.product = product
            ingredient.save()


class CFSScheduleTemplateDeleteView(CFSTemplatePermissionRequiredMixin, LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        schedule_template = get_cfs_schedule_template(**kwargs)
        schedule_template.delete()

        return redirect(
            reverse("cat:edit-step", kwargs={"cat_pk": self.kwargs["cat_pk"], "step": CatSteps.CFS})
        )


class CFSManufacturerUpdateView(LoginRequiredMixin, CFSTemplatePermissionRequiredMixin, UpdateView):
    form_class = CFSManufacturerDetailsTemplateForm
    template_name = "web/domains/cat/cfs/manufacturer-update.html"

    def get_object(self, queryset: CFSScheduleTemplate | None = None) -> CFSScheduleTemplate:
        return get_cfs_schedule_template(**self.kwargs)

    def get_success_url(self) -> str:
        return reverse(
            "cat:edit-step-related",
            kwargs={
                "cat_pk": self.kwargs["cat_pk"],
                "step": CatSteps.CFS_SCHEDULE,
                "step_pk": self.object.pk,
            },
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        return context | {
            "page_title": "Edit Manufacturer",
            "previous_link": self.get_success_url(),
        }


class CFSManufacturerDeleteView(CFSTemplatePermissionRequiredMixin, LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        schedule = get_cfs_schedule_template(**kwargs)

        schedule.manufacturer_name = None
        schedule.manufacturer_address_entry_type = AddressEntryType.MANUAL
        schedule.manufacturer_postcode = None
        schedule.manufacturer_address = None
        schedule.save()

        return redirect(
            reverse(
                "cat:edit-step-related",
                kwargs={
                    "cat_pk": self.kwargs["cat_pk"],
                    "step": CatSteps.CFS_SCHEDULE,
                    "step_pk": schedule.pk,
                },
            )
        )


class CFSScheduleTemplateProductCreateView(
    CFSTemplatePermissionRequiredMixin, LoginRequiredMixin, CreateView
):
    form_class = CFSProductTemplateForm
    template_name = "web/domains/cat/cfs/product-template-create.html"

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        return kwargs | {"schedule": get_cfs_schedule_template(**self.kwargs)}

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        return context | {
            "page_title": "Add Product",
            "previous_link": self.get_edit_schedule_url(),
        }

    def get_success_url(self) -> str:
        return reverse(
            "cat:cfs-schedule-product-update",
            kwargs={
                "cat_pk": self.kwargs["cat_pk"],
                "schedule_template_pk": self.kwargs["schedule_template_pk"],
                "product_template_pk": self.object.pk,
            },
        )

    def get_edit_schedule_url(self) -> str:
        return reverse(
            "cat:edit-step-related",
            kwargs={
                "cat_pk": self.kwargs["cat_pk"],
                "step": CatSteps.CFS_SCHEDULE,
                "step_pk": self.kwargs["schedule_template_pk"],
            },
        )


class CFSScheduleTemplateProductCreateMultipleView(
    CFSTemplatePermissionRequiredMixin, LoginRequiredMixin, InlineFormsetView
):
    # parent model config
    model = CFSScheduleTemplate
    pk_url_kwarg = "schedule_template_pk"

    # Inline formset config
    formset_class = CFSProductTemplateFormSet
    template_name = "web/domains/cat/cfs/product-template-create-multiple.html"

    def get_success_url(self) -> str:
        return reverse(
            "cat:edit-step-related",
            kwargs={
                "cat_pk": self.kwargs["cat_pk"],
                "step": CatSteps.CFS_SCHEDULE,
                "step_pk": self.object.pk,
            },
        )

    def get_formset_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_formset_kwargs()

        # Exclude existing related products as this is a create view.
        queryset = CFSProductTemplateFormSet.model.objects.none()

        return kwargs | {"queryset": queryset}

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        return context | {
            "page_title": "Add Products",
            "previous_link": self.get_success_url(),
        }


class CFSScheduleTemplateProductUpdateView(
    CFSTemplatePermissionRequiredMixin, LoginRequiredMixin, UpdateView
):
    form_class = CFSProductTemplateForm
    template_name = "web/domains/cat/cfs/product-template-update.html"

    # extra type hints
    object: CFSProductTemplate
    pt_formset: CFSProductTypeTemplateFormSet
    ai_formset: CFSActiveIngredientTemplateFormSet

    def get_object(self, queryset: CFSProductTemplate | None = None) -> CFSProductTemplate:
        return get_cfs_schedule_product(**self.kwargs)

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        return kwargs | {"schedule": self.object.schedule}

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        return context | {
            "page_title": "Update Product",
            "previous_link": self.get_edit_schedule_url(),
            "is_biocidal": self.object.schedule.is_biocidal(),
            "pt_formset": self.pt_formset,
            "ai_formset": self.ai_formset,
        }

    def get(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        self._set_formsets()

        return super().get(request, *args, **kwargs)

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        self._set_formsets()
        form = self.get_form()
        form_valid = form.is_valid()

        if self.object.schedule.is_biocidal():
            # Evaluate all form.is_valid() methods so we see all errors.
            pt_formset_valid = self.pt_formset.is_valid()
            ai_formset_valid = self.ai_formset.is_valid()

            all_forms_valid = form_valid and pt_formset_valid and ai_formset_valid
        else:
            all_forms_valid = form_valid

        if all_forms_valid:
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form: CFSProductTemplateForm) -> HttpResponse:
        form.save()

        if self.object.schedule.is_biocidal():
            self.pt_formset.save()
            self.ai_formset.save()

        return redirect(self.get_success_url())

    def _set_formsets(self) -> None:
        """Prefix needs to be the same for GET and POST to work correctly."""
        self.pt_formset = CFSProductTypeTemplateFormSet(
            self.request.POST or None, instance=self.object, prefix="pt_"
        )
        self.ai_formset = CFSActiveIngredientTemplateFormSet(
            self.request.POST or None, instance=self.object, prefix="ai_"
        )

    def get_success_url(self) -> str:
        return reverse(
            "cat:cfs-schedule-product-update",
            kwargs={
                "cat_pk": self.kwargs["cat_pk"],
                "schedule_template_pk": self.kwargs["schedule_template_pk"],
                "product_template_pk": self.object.pk,
            },
        )

    def get_edit_schedule_url(self) -> str:
        return reverse(
            "cat:edit-step-related",
            kwargs={
                "cat_pk": self.kwargs["cat_pk"],
                "step": CatSteps.CFS_SCHEDULE,
                "step_pk": self.kwargs["schedule_template_pk"],
            },
        )


class CFSScheduleTemplateProductDeleteView(
    CFSTemplatePermissionRequiredMixin, LoginRequiredMixin, View
):
    http_method_names = ["post"]

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        product = get_cfs_schedule_product(**kwargs)
        product.delete()

        return redirect(
            reverse(
                "cat:edit-step-related",
                kwargs={
                    "cat_pk": self.kwargs["cat_pk"],
                    "step": CatSteps.CFS_SCHEDULE,
                    "step_pk": self.kwargs["schedule_template_pk"],
                },
            )
        )


class CFSScheduleTemplateProductDownloadSpreadsheetView(
    CFSTemplatePermissionRequiredMixin, LoginRequiredMixin, View
):
    http_method_names = ["get"]

    def get(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        schedule = get_cfs_schedule_template(**self.kwargs)
        return get_product_spreadsheet_response(schedule)


class CFSScheduleTemplateProductUploadSpreadsheetView(
    CFSTemplatePermissionRequiredMixin, LoginRequiredMixin, FormView
):
    """Post only FormView for processing a product template spreadsheet.

    Always redirects to the success_url.
    """

    form_class = ProductsFileUploadForm
    http_method_names = ["post"]

    def form_valid(self, form: ProductsFileUploadForm) -> HttpResponseRedirect:
        schedule_template = get_cfs_schedule_template(**self.kwargs)

        products_file = form.cleaned_data["file"]

        try:
            product_count = process_products_file(products_file, schedule_template)
            messages.success(
                self.request, f"Upload Success: {product_count} products uploaded successfully"
            )

        except ValidationError as err:
            messages.warning(self.request, f"Upload failed: {err}")

        except Exception:
            messages.warning(self.request, "Upload failed: An unknown error occurred")
            capture_exception()

        finally:
            products_file = self.request.FILES.get("file")

            if products_file:
                delete_file_from_s3(products_file.name)

        return super().form_valid(form)

    def form_invalid(self, form: ProductsFileUploadForm) -> HttpResponseRedirect:
        if form.errors and "file" in form.errors:
            err = form.errors["file"][0]
        else:
            err = "No valid file found. Please upload the spreadsheet."

        messages.warning(self.request, f"Upload failed: {err}")

        return redirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse(
            "cat:edit-step-related",
            kwargs={
                "cat_pk": self.kwargs["cat_pk"],
                "step": CatSteps.CFS_SCHEDULE,
                "step_pk": self.kwargs["schedule_template_pk"],
            },
        )


def get_cfs_schedule_template(
    *, cat_pk: int, schedule_template_pk: int, **kwargs: Any
) -> CFSScheduleTemplate:
    """Securely load a CFSScheduleTemplate instance using common view kwargs."""

    try:
        cat = CertificateApplicationTemplate.objects.get(pk=cat_pk)
        return cat.cfs_template.schedules.filter(pk=schedule_template_pk).get()
    except ObjectDoesNotExist:
        raise PermissionDenied


def get_cfs_schedule_product(
    *, cat_pk: int, schedule_template_pk: int, product_template_pk: int, **kwargs: Any
) -> CFSProductTemplate:
    """Securely load a CFSProductTemplate instance using common view kwargs."""

    schedule = get_cfs_schedule_template(cat_pk=cat_pk, schedule_template_pk=schedule_template_pk)

    try:
        return schedule.products.filter(pk=product_template_pk).get()
    except ObjectDoesNotExist:
        raise PermissionDenied
