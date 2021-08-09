from typing import List, NamedTuple, Type

import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from guardian.shortcuts import get_objects_for_user

from web.domains.case.forms import SubmitForm
from web.domains.case.views import check_application_permission
from web.domains.exporter.models import Exporter
from web.domains.user.models import User
from web.flow.models import Task
from web.types import AuthenticatedHttpRequest
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from .forms import (
    CFSActiveIngredientForm,
    CFSManufacturerDetailsForm,
    CFSProductForm,
    CFSProductTypeForm,
    CreateExportApplicationForm,
    EditCFScheduleForm,
    EditCFSForm,
    PrepareCertManufactureForm,
)
from .models import (
    CertificateOfFreeSaleApplication,
    CertificateOfManufactureApplication,
    CFSProduct,
    CFSProductActiveIngredient,
    CFSProductType,
    CFSSchedule,
    ExportApplication,
    ExportApplicationType,
)

logger = logging.get_logger(__name__)


class ExportApplicationChoiceView(PermissionRequiredMixin, TemplateView):
    template_name = "web/domains/case/export/choose.html"
    permission_required = "web.exporter_access"


class CreateExportApplicationConfig(NamedTuple):
    model_class: Type[ExportApplication]
    form_class: Type[CreateExportApplicationForm]
    certificate_message: str


def _exporters_with_agents(user: User) -> List[int]:
    exporters_with_agents = get_objects_for_user(user, ["web.is_agent_of_exporter"], Exporter)
    return [exporter.pk for exporter in exporters_with_agents]


@login_required
@permission_required("web.exporter_access", raise_exception=True)
def create_export_application(request: AuthenticatedHttpRequest, *, type_code: str) -> HttpResponse:
    application_type: ExportApplicationType = ExportApplicationType.objects.get(type_code=type_code)

    config = _get_export_app_config(type_code)

    if request.POST:
        form = config.form_class(request.POST, user=request.user)

        if form.is_valid():
            application = config.model_class()
            application.exporter = form.cleaned_data["exporter"]
            application.exporter_office = form.cleaned_data["exporter_office"]
            application.agent = form.cleaned_data["agent"]
            application.agent_office = form.cleaned_data["agent_office"]
            application.process_type = config.model_class.PROCESS_TYPE
            application.created_by = request.user
            application.last_updated_by = request.user
            application.submitted_by = request.user
            application.application_type = application_type

            with transaction.atomic():
                application.save()
                Task.objects.create(process=application, task_type="prepare", owner=request.user)

            return redirect(
                reverse(application.get_edit_view_name(), kwargs={"application_pk": application.pk})
            )
    else:
        form = config.form_class(user=request.user)

    context = {
        "form": form,
        "export_application_type": application_type,
        "certificate_message": config.certificate_message,
        "application_title": ExportApplicationType.ProcessTypes(
            config.model_class.PROCESS_TYPE
        ).label,
        "exporters_with_agents": _exporters_with_agents(request.user),
    }

    return render(request, "web/domains/case/export/create.html", context)


def _get_export_app_config(type_code: str) -> CreateExportApplicationConfig:
    if type_code == ExportApplicationType.Types.MANUFACTURE:
        return CreateExportApplicationConfig(
            model_class=CertificateOfManufactureApplication,
            form_class=CreateExportApplicationForm,
            certificate_message=(
                "Certificates of Manufacture are applicable only to pesticides that are for export"
                " only and not on free sale on the domestic market."
            ),
        )

    elif type_code == ExportApplicationType.Types.FREE_SALE:
        return CreateExportApplicationConfig(
            model_class=CertificateOfFreeSaleApplication,
            form_class=CreateExportApplicationForm,
            certificate_message=(
                "If you are supplying the product to a client in the UK/EU then you do not require a certificate."
                " Your client will need to apply for a certificate if they subsequently export it to one of their"
                " clients outside of the EU.\n\n"
                "DIT does not issue Certificates of Free Sale for food, foodsupplements, pesticides and CE marked medical devices."
            ),
        )

    raise NotImplementedError(f"type_code not supported: {type_code}")


@login_required
def edit_com(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfManufactureApplication = get_object_or_404(
            CertificateOfManufactureApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = PrepareCertManufactureForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("export:com-edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = PrepareCertManufactureForm(
                instance=application, initial={"contact": request.user}
            )

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
        }

        return render(request, "web/domains/case/export/prepare-com.html", context)


@login_required
def submit_com(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfManufactureApplication = get_object_or_404(
            CertificateOfManufactureApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        errors = ApplicationErrors()
        page_errors = PageErrors(
            page_name="Application details",
            url=reverse("export:com-edit", kwargs={"application_pk": application_pk}),
        )
        create_page_errors(
            PrepareCertManufactureForm(data=model_to_dict(application), instance=application),
            page_errors,
        )
        errors.add(page_errors)

        if request.POST:
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                application.submit_application(request, task)

                return application.redirect_after_submit(request)

        else:
            form = SubmitForm()

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "exporter_name": application.exporter.name,
            "form": form,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/export/submit-com.html", context)


@login_required
def edit_cfs(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = EditCFSForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("export:cfs-edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditCFSForm(instance=application, initial={"contact": request.user})

        schedules = application.schedules.filter(is_active=True).order_by("created_at")
        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "schedules": schedules,
        }

        return render(request, "web/domains/case/export/edit-cfs.html", context)


@login_required
@require_POST
def cfs_add_schedule(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        new_schedule = application.schedules.create(created_by=request.user)

        return redirect(
            reverse(
                "export:cfs-schedule-edit",
                kwargs={"application_pk": application_pk, "schedule_pk": new_schedule.pk},
            )
        )


@login_required
def cfs_edit_schedule(
    request: AuthenticatedHttpRequest, *, application_pk: int, schedule_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        if request.POST:
            form = EditCFScheduleForm(data=request.POST, instance=schedule)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "export:cfs-schedule-edit",
                        kwargs={"application_pk": application_pk, "schedule_pk": schedule.pk},
                    )
                )

        else:
            form = EditCFScheduleForm(instance=schedule)

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Edit Schedule",
            "schedule": schedule,
            "products": schedule.products.order_by("pk").all(),
            "has_legislation": schedule.legislations.exists(),
            "is_biocidal": schedule.legislations.filter(is_biocidal=True).exists(),
        }

        return render(request, "web/domains/case/export/edit-cfs-schedule.html", context)


@require_POST
@login_required
def cfs_delete_schedule(
    request: AuthenticatedHttpRequest, *, application_pk: int, schedule_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule = application.schedules.get(pk=schedule_pk)
        schedule.is_active = False
        schedule.save()

        return redirect(reverse("export:cfs-edit", kwargs={"application_pk": application_pk}))


@login_required
def cfs_set_manufacturer(
    request: AuthenticatedHttpRequest, *, application_pk: int, schedule_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        if request.POST:
            form = CFSManufacturerDetailsForm(data=request.POST, instance=schedule)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "export:cfs-schedule-edit",
                        kwargs={"application_pk": application_pk, "schedule_pk": schedule.pk},
                    )
                )

        else:
            form = CFSManufacturerDetailsForm(instance=schedule)

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Edit Manufacturer",
        }

        return render(request, "web/domains/case/export/cfs-manufacturer-address.html", context)


@require_POST
@login_required
def cfs_delete_manufacturer(
    request: AuthenticatedHttpRequest, *, application_pk: int, schedule_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        schedule.manufacturer_name = None
        schedule.manufacturer_address_entry_type = CFSSchedule.AddressEntryType.MANUAL
        schedule.manufacturer_postcode = None
        schedule.manufacturer_address = None
        schedule.save()

        return redirect(
            reverse(
                "export:cfs-schedule-edit",
                kwargs={"application_pk": application_pk, "schedule_pk": schedule.pk},
            )
        )


@login_required
def cfs_add_product(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    schedule_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        if request.POST:
            form = CFSProductForm(data=request.POST, schedule=schedule)

            if form.is_valid():
                product = form.save()
                is_biocidal = schedule.legislations.filter(is_biocidal=True).exists()

                if not is_biocidal:
                    return redirect(
                        reverse(
                            "export:cfs-schedule-edit",
                            kwargs={"application_pk": application_pk, "schedule_pk": schedule.pk},
                        )
                    )

                return redirect(
                    reverse(
                        "export:cfs-schedule-edit-product",
                        kwargs={
                            "application_pk": application_pk,
                            "schedule_pk": schedule.pk,
                            "product_pk": product.pk,
                        },
                    )
                )

        else:
            form = CFSProductForm(schedule=schedule)

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "schedule": schedule,
            "form": form,
            "page_title": "Add Product",
        }

        return render(request, "web/domains/case/export/cfs-edit-product.html", context)


@login_required
def cfs_edit_product(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    schedule_pk: int,
    product_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        product: CFSProduct = get_object_or_404(
            schedule.products.select_for_update(), pk=product_pk
        )

        is_biocidal = schedule.legislations.filter(is_biocidal=True).exists()

        if request.POST:
            form = CFSProductForm(data=request.POST, instance=product, schedule=schedule)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "export:cfs-schedule-edit",
                        kwargs={"application_pk": application_pk, "schedule_pk": schedule.pk},
                    )
                )

        else:
            form = CFSProductForm(instance=product, schedule=schedule)

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "schedule": schedule,
            "form": form,
            "page_title": "Edit Product",
            "product": product,
            "is_biocidal": is_biocidal,
            "product_type_numbers": product.product_type_numbers.all(),
            "ingredients": product.active_ingredients.all(),
        }

        return render(request, "web/domains/case/export/cfs-edit-product.html", context)


@require_POST
@login_required
def cfs_delete_product(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    schedule_pk: int,
    product_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        schedule.products.filter(pk=product_pk).delete()

        return redirect(
            reverse(
                "export:cfs-schedule-edit",
                kwargs={"application_pk": application_pk, "schedule_pk": schedule.pk},
            )
        )


@login_required
def cfs_add_ingredient(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    schedule_pk: int,
    product_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        product: CFSProduct = get_object_or_404(
            schedule.products.select_for_update(), pk=product_pk
        )

        if request.POST:
            form = CFSActiveIngredientForm(data=request.POST, product=product)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "export:cfs-schedule-edit-product",
                        kwargs={
                            "application_pk": application_pk,
                            "schedule_pk": schedule.pk,
                            "product_pk": product.pk,
                        },
                    )
                )

        else:
            form = CFSActiveIngredientForm(product=product)

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "schedule": schedule,
            "form": form,
            "product": product,
            "page_title": "Add Active Ingredient",
        }

        return render(request, "web/domains/case/export/cfs-edit-product-child.html", context)


@login_required
def cfs_edit_ingredient(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    schedule_pk: int,
    product_pk: int,
    ingredient_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        product: CFSProduct = get_object_or_404(
            schedule.products.select_for_update(), pk=product_pk
        )

        ingredient: CFSProductActiveIngredient = get_object_or_404(
            product.active_ingredients.select_for_update(), pk=ingredient_pk
        )

        if request.POST:
            form = CFSActiveIngredientForm(data=request.POST, instance=ingredient, product=product)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "export:cfs-schedule-edit-product",
                        kwargs={
                            "application_pk": application_pk,
                            "schedule_pk": schedule.pk,
                            "product_pk": product.pk,
                        },
                    )
                )

        else:
            form = CFSActiveIngredientForm(instance=ingredient, product=product)

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "schedule": schedule,
            "product": product,
            "instance": ingredient,
            "form": form,
            "page_title": "Edit Active Ingredient",
            "type": "ingredient",
        }

        return render(request, "web/domains/case/export/cfs-edit-product-child.html", context)


@require_POST
@login_required
def cfs_delete_ingredient(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    schedule_pk: int,
    product_pk: int,
    ingredient_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        product: CFSProduct = get_object_or_404(
            schedule.products.select_for_update(), pk=product_pk
        )

        product.active_ingredients.filter(pk=ingredient_pk).delete()

        return redirect(
            reverse(
                "export:cfs-schedule-edit-product",
                kwargs={
                    "application_pk": application_pk,
                    "schedule_pk": schedule.pk,
                    "product_pk": product.pk,
                },
            )
        )


@login_required
def cfs_add_product_type(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    schedule_pk: int,
    product_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        product: CFSProduct = get_object_or_404(
            schedule.products.select_for_update(), pk=product_pk
        )

        if request.POST:
            form = CFSProductTypeForm(data=request.POST, product=product)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "export:cfs-schedule-edit-product",
                        kwargs={
                            "application_pk": application_pk,
                            "schedule_pk": schedule.pk,
                            "product_pk": product.pk,
                        },
                    )
                )

        else:
            form = CFSProductTypeForm(product=product)

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "schedule": schedule,
            "form": form,
            "product": product,
            "page_title": "Add Product Type Number",
        }

        return render(request, "web/domains/case/export/cfs-edit-product-child.html", context)


@login_required
def cfs_edit_product_type(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    schedule_pk: int,
    product_pk: int,
    product_type_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        product: CFSProduct = get_object_or_404(
            schedule.products.select_for_update(), pk=product_pk
        )

        product_type: CFSProductType = get_object_or_404(
            product.product_type_numbers.select_for_update(), pk=product_type_pk
        )

        if request.POST:
            form = CFSProductTypeForm(data=request.POST, instance=product_type, product=product)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "export:cfs-schedule-edit-product",
                        kwargs={
                            "application_pk": application_pk,
                            "schedule_pk": schedule.pk,
                            "product_pk": product.pk,
                        },
                    )
                )

        else:
            form = CFSProductTypeForm(instance=product_type, product=product)

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "schedule": schedule,
            "product": product,
            "instance": product_type,
            "form": form,
            "page_title": "Edit Product Type Number",
            "type": "product_type",
        }

        return render(request, "web/domains/case/export/cfs-edit-product-child.html", context)


@require_POST
@login_required
def cfs_delete_product_type(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    schedule_pk: int,
    product_pk: int,
    product_type_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        product: CFSProduct = get_object_or_404(
            schedule.products.select_for_update(), pk=product_pk
        )

        product.product_type_numbers.filter(pk=product_type_pk).delete()

        return redirect(
            reverse(
                "export:cfs-schedule-edit-product",
                kwargs={
                    "application_pk": application_pk,
                    "schedule_pk": schedule.pk,
                    "product_pk": product.pk,
                },
            )
        )


@login_required
def cfs_copy_schedule(
    request: AuthenticatedHttpRequest, *, application_pk: int, schedule_pk: int
) -> HttpResponse:
    """Copy an application schedule.

    How to copy a model instance
    https://docs.djangoproject.com/en/3.2/topics/db/queries/#copying-model-instances
    """
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        schedule_to_copy: CFSSchedule = get_object_or_404(application.schedules, pk=schedule_pk)

        # ManyToMany you can just use `.all()` to get the records
        # ForeignKeys you have to fetch from the db before the save.
        legislations_to_copy = schedule_to_copy.legislations.all()
        products_to_copy = [p for p in schedule_to_copy.products.all().order_by("pk")]

        schedule_to_copy.pk = None
        schedule_to_copy.created_by = request.user
        schedule_to_copy.save()

        # Copy the legislation records
        schedule_to_copy.legislations.set(legislations_to_copy)

        # copy the product records
        for product in products_to_copy:
            product_types_to_copy = [pt for pt in product.product_type_numbers.all().order_by("pk")]
            ingredients_to_copy = [i for i in product.active_ingredients.all().order_by("pk")]

            product.pk = None
            product.schedule = schedule_to_copy
            product.save()

            for ptn in product_types_to_copy:
                ptn.pk = None
                ptn.product = product
                ptn.save()

            for ingredient in ingredients_to_copy:
                ingredient.pk = None
                ingredient.product = product
                ingredient.save()

        # Add the copied schedule to the application
        application.schedules.add(schedule_to_copy)

        return redirect(
            reverse(
                "export:cfs-schedule-edit",
                kwargs={"application_pk": application_pk, "schedule_pk": schedule_to_copy.pk},
            )
        )


@login_required
def submit_cfs(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "export")

        task = application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        errors = _get_cfs_errors(application)

        if request.POST:
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                application.submit_application(request, task)

                return application.redirect_after_submit(request)

        else:
            form = SubmitForm()

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "exporter_name": application.exporter.name,
            "form": form,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/export/submit-cfs.html", context)


def _get_cfs_errors(application: CertificateOfFreeSaleApplication) -> ApplicationErrors:
    """Get all Certificate of free sale errors before submitting the application."""
    errors = ApplicationErrors()
    page_errors = PageErrors(
        page_name="Application details",
        url=reverse("export:cfs-edit", kwargs={"application_pk": application.pk}),
    )
    create_page_errors(
        EditCFSForm(data=model_to_dict(application), instance=application), page_errors
    )

    # Error checks related to schedules.
    active_schedules = application.schedules.filter(is_active=True).order_by("created_at")
    if not active_schedules.exists():
        page_errors.add(
            FieldError(field_name="Schedule", messages=["At least one schedule must be added"])
        )

    else:
        for idx, schedule in enumerate(active_schedules, start=1):
            schedule_page_errors = PageErrors(
                page_name=f"Schedule {idx}",
                url=reverse(
                    "export:cfs-schedule-edit",
                    kwargs={"application_pk": application.pk, "schedule_pk": schedule.pk},
                ),
            )
            create_page_errors(
                EditCFScheduleForm(data=model_to_dict(schedule), instance=schedule),
                schedule_page_errors,
            )

            errors.add(schedule_page_errors)

            # Check that the schedule has products
            if not schedule.products.exists():
                product_page_errors = PageErrors(
                    page_name=f"Schedule {idx} - Product",
                    url=reverse(
                        "export:cfs-schedule-add-product",
                        kwargs={
                            "application_pk": application.pk,
                            "schedule_pk": schedule.pk,
                        },
                    ),
                )

                product_page_errors.add(
                    FieldError(
                        field_name="Products", messages=["At least one product must be added"]
                    )
                )

                errors.add(product_page_errors)
                continue

            is_biocidal = schedule.legislations.filter(is_biocidal=True).exists()

            if not is_biocidal:
                continue

            # Check all the products are valid for biocidal legislation CFS schedules
            for product in schedule.products.all():
                product_page_errors = PageErrors(
                    page_name=f"Schedule {idx} - Product {product.product_name}",
                    url=reverse(
                        "export:cfs-schedule-edit-product",
                        kwargs={
                            "application_pk": application.pk,
                            "schedule_pk": schedule.pk,
                            "product_pk": product.pk,
                        },
                    ),
                )

                if not product.product_type_numbers.exists():
                    product_page_errors.add(
                        FieldError(
                            field_name="Product Type Numbers",
                            messages=["Product type numbers must be specified on all product"],
                        )
                    )

                if not product.active_ingredients.exists():
                    product_page_errors.add(
                        FieldError(
                            field_name="Active Ingredients",
                            messages=["Active Ingredients must be specified on all products"],
                        )
                    )

                errors.add(product_page_errors)

    errors.add(page_errors)

    return errors
