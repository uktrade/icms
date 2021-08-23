from typing import List, NamedTuple, Type

import structlog as logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView
from guardian.shortcuts import get_objects_for_user

from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.views import (
    check_application_permission,
    get_application_current_task,
    view_application_file,
)
from web.domains.exporter.models import Exporter
from web.domains.file.utils import create_file_model
from web.domains.user.models import User
from web.flow.models import Task
from web.models.shared import YesNoChoices
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import delete_file_from_s3
from web.utils.sentry import capture_exception
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
    EditGMPForm,
    GMPBrandForm,
    PrepareCertManufactureForm,
    ProductsFileUploadForm,
)
from .models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    CFSProduct,
    CFSProductActiveIngredient,
    CFSProductType,
    CFSSchedule,
    ExportApplication,
    ExportApplicationType,
    GMPFile,
    ProductLegislation,
)
from .utils import CustomError, generate_product_template_xlsx, process_products_file

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

                # GMP applications are for China only
                if application_type.type_code == ExportApplicationType.Types.GMP:
                    country = application_type.country_group.countries.filter(
                        is_active=True
                    ).first()
                    application.countries.add(country)

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
        "case_type": "export",
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

    elif type_code == ExportApplicationType.Types.GMP:
        return CreateExportApplicationConfig(
            model_class=CertificateOfGoodManufacturingPracticeApplication,
            form_class=CreateExportApplicationForm,
            certificate_message="",
        )

    raise NotImplementedError(f"type_code not supported: {type_code}")


@login_required
def edit_com(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfManufactureApplication = get_object_or_404(
            CertificateOfManufactureApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = get_application_current_task(application, "export", "prepare")

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
            "case_type": "export",
        }

        return render(request, "web/domains/case/export/prepare-com.html", context)


@login_required
def submit_com(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfManufactureApplication = get_object_or_404(
            CertificateOfManufactureApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = get_application_current_task(application, "export", "prepare")

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

        errors.add(get_org_update_request_errors(application, "export"))

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
            "case_type": "export",
        }

        return render(request, "web/domains/case/export/submit-com.html", context)


@login_required
def edit_cfs(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        task = get_application_current_task(application, "export", "prepare")

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
            "case_type": "export",
        }

        return render(request, "web/domains/case/export/cfs-edit.html", context)


@login_required
@require_POST
def cfs_add_schedule(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "export")
        get_application_current_task(application, "export", "prepare")

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
        task = get_application_current_task(application, "export", "prepare")

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

        schedule_legislations = schedule.legislations.filter(is_active=True)

        has_cosmetics = schedule_legislations.filter(is_eu_cosmetics_regulation=True).exists()
        not_export_only = schedule.goods_export_only == YesNoChoices.no
        show_schedule_statements_is_responsible_person = has_cosmetics and not_export_only

        legislation_config = {
            legislation.pk: {"isEUCosmeticsRegulation": legislation.is_eu_cosmetics_regulation}
            for legislation in ProductLegislation.objects.filter(is_active=True)
        }

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Edit Schedule",
            "schedule": schedule,
            "is_biocidal": schedule.is_biocidal(),
            "products": schedule.products.order_by("pk").all(),
            "product_upload_form": ProductsFileUploadForm(),
            "has_legislation": schedule_legislations.exists(),
            "case_type": "export",
            "legislation_config": legislation_config,
            "show_schedule_statements_is_responsible_person": show_schedule_statements_is_responsible_person,
        }

        return render(request, "web/domains/case/export/cfs-edit-schedule.html", context)


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
        get_application_current_task(application, "export", "prepare")

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
        task = get_application_current_task(application, "export", "prepare")

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
            "schedule": schedule,
            "task": task,
            "form": form,
            "page_title": "Edit Manufacturer",
            "case_type": "export",
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
        get_application_current_task(application, "export", "prepare")

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
        task = get_application_current_task(application, "export", "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        if request.POST:
            form = CFSProductForm(data=request.POST, schedule=schedule)

            if form.is_valid():
                product = form.save()

                if schedule.is_biocidal():
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

                return redirect(
                    reverse(
                        "export:cfs-schedule-edit",
                        kwargs={"application_pk": application_pk, "schedule_pk": schedule.pk},
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
            "case_type": "export",
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
        task = get_application_current_task(application, "export", "prepare")

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        product: CFSProduct = get_object_or_404(
            schedule.products.select_for_update(), pk=product_pk
        )

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
            "is_biocidal": schedule.is_biocidal(),
            "product": product,
            "product_type_numbers": product.product_type_numbers.all(),
            "ingredients": product.active_ingredients.all(),
            "case_type": "export",
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
        get_application_current_task(application, "export", "prepare")

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
        task = get_application_current_task(application, "export", "prepare")

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
            "case_type": "export",
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
        task = get_application_current_task(application, "export", "prepare")

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
            "case_type": "export",
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
        get_application_current_task(application, "export", "prepare")

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
        task = get_application_current_task(application, "export", "prepare")

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
            "case_type": "export",
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
        task = get_application_current_task(application, "export", "prepare")

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
            "case_type": "export",
        }

        return render(request, "web/domains/case/export/cfs-edit-product-child.html", context)


@login_required
def product_spreadsheet_download_template(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    schedule_pk: int,
) -> HttpResponse:
    application: CertificateOfFreeSaleApplication = get_object_or_404(
        CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
    )
    check_application_permission(application, request.user, "export")
    application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

    schedule: CFSSchedule = get_object_or_404(
        CFSSchedule.objects.select_for_update(), pk=schedule_pk
    )

    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    response = HttpResponse(content_type=mime_type)
    is_biocidal = schedule.is_biocidal()
    workbook = generate_product_template_xlsx(is_biocidal)
    response.write(workbook)

    filename = "CFS Product Upload Template.xlsx"

    if is_biocidal:
        filename = "CFS Product Upload Biocide Template.xlsx"

    response["Content-Disposition"] = f"attachment; filename={filename}"

    return response


@require_POST
@login_required
def product_spreadsheet_upload(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    schedule_pk: int,
) -> HttpResponse:
    try:
        with transaction.atomic():
            application: CertificateOfFreeSaleApplication = get_object_or_404(
                CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
            )
            check_application_permission(application, request.user, "export")
            application.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

            schedule: CFSSchedule = get_object_or_404(
                CFSSchedule.objects.select_for_update(), pk=schedule_pk
            )

            form = ProductsFileUploadForm(request.POST, request.FILES)

            if form.is_valid():
                products_file = form.cleaned_data["file"]
                product_count = process_products_file(products_file, schedule)
                messages.success(
                    request, f"Upload Success: {product_count} products uploaded successfully"
                )

            else:
                if form.errors and "file" in form.errors:
                    err = form.errors["file"][0]
                else:
                    err = "No valid file found. Please upload the spreadsheet."

                messages.warning(request, f"Upload failed: {err}")

    except CustomError as err:
        messages.warning(request, f"Upload failed: {err}")

    except Exception:
        messages.warning(request, "Upload failed: An unknown error occurred")
        capture_exception()

    finally:
        products_file = request.FILES.get("file")

        if products_file:
            delete_file_from_s3(products_file.name)

    return redirect(
        reverse(
            "export:cfs-schedule-edit",
            kwargs={"application_pk": application_pk, "schedule_pk": schedule.pk},
        )
    )


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
        get_application_current_task(application, "export", "prepare")

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
        get_application_current_task(application, "export", "prepare")

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

        task = get_application_current_task(application, "export", "prepare")

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
            "case_type": "export",
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

            if not schedule.is_biocidal():
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

    errors.add(get_org_update_request_errors(application, "export"))

    return errors


@login_required
def edit_gmp(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfGoodManufacturingPracticeApplication = get_object_or_404(
            CertificateOfGoodManufacturingPracticeApplication.objects.select_for_update(),
            pk=application_pk,
        )

        check_application_permission(application, request.user, "export")

        task = get_application_current_task(application, "export", "prepare")

        if request.POST:
            form = EditGMPForm(data=request.POST, instance=application)

            if form.is_valid():
                application = form.save(commit=False)

                application_files = GMPFile.objects.filter(
                    certificateofgoodmanufacturingpracticeapplication=application, is_active=True
                )
                ft = GMPFile.Type

                if application.gmp_certificate_issued == application.CertificateTypes.ISO_22716:
                    application_files.filter(file_type=ft.BRC_GSOCP).update(is_active=False)

                elif application.gmp_certificate_issued == application.CertificateTypes.BRC_GSOCP:
                    application_files.filter(
                        file_type__in=[ft.ISO_22716, ft.ISO_17021, ft.ISO_17065]
                    ).update(is_active=False)

                    application.auditor_accredited = None
                    application.auditor_certified = None

                application.save()

                return redirect(
                    reverse("export:gmp-edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditGMPForm(instance=application, initial={"contact": request.user})

        form_valid = EditGMPForm(data=model_to_dict(application), instance=application).is_valid()
        show_iso_table = (
            form_valid
            and application.gmp_certificate_issued == application.CertificateTypes.ISO_22716
        )
        show_brc_table = (
            form_valid
            and application.gmp_certificate_issued == application.CertificateTypes.BRC_GSOCP
        )

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "case_type": "export",
            "country": application.countries.first(),
            "GMPFileTypes": GMPFile.Type,
            "show_iso_table": show_iso_table,
            "show_brc_table": show_brc_table,
        }

        return render(request, "web/domains/case/export/gmp-edit.html", context)


@login_required
def add_gmp_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, file_type: str
) -> HttpResponse:
    gmp_edit: str = reverse("export:gmp-edit", kwargs={"application_pk": application_pk})
    prev_link = gmp_edit + "#gmp-document-list"

    with transaction.atomic():
        application: CertificateOfGoodManufacturingPracticeApplication = get_object_or_404(
            CertificateOfGoodManufacturingPracticeApplication.objects.select_for_update(),
            pk=application_pk,
        )

        check_application_permission(application, request.user, "export")

        task = get_application_current_task(application, "export", "prepare")

        if request.POST:
            form = DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")

                create_file_model(
                    document,
                    request.user,
                    application.supporting_documents,
                    extra_args={"file_type": file_type},
                )

                return redirect(prev_link)
        else:
            form = DocumentForm()

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": f"Certificate of Good Manufacturing Practice - Add {GMPFile.Type[file_type].label} document",  # type: ignore[misc]
            "prev_link": prev_link,
        }

        return render(request, "web/domains/case/export/add_supporting_document.html", context)


@require_GET
@login_required
def view_gmp_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application: CertificateOfGoodManufacturingPracticeApplication = get_object_or_404(
        CertificateOfGoodManufacturingPracticeApplication, pk=application_pk
    )

    return view_application_file(
        request.user, application, application.supporting_documents, document_pk, "export"
    )


@require_POST
@login_required
def delete_gmp_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfGoodManufacturingPracticeApplication = get_object_or_404(
            CertificateOfGoodManufacturingPracticeApplication.objects.select_for_update(),
            pk=application_pk,
        )

        check_application_permission(application, request.user, "export")

        get_application_current_task(application, "export", "prepare")

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        prev_link = reverse("export:gmp-edit", kwargs={"application_pk": application_pk})

        return redirect(prev_link)


@login_required
def submit_gmp(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfGoodManufacturingPracticeApplication = get_object_or_404(
            CertificateOfGoodManufacturingPracticeApplication.objects.select_for_update(),
            pk=application_pk,
        )
        check_application_permission(application, request.user, "export")
        task = get_application_current_task(application, "export", "prepare")

        errors = ApplicationErrors()
        page_errors = PageErrors(
            page_name="Application details",
            url=reverse("export:gmp-edit", kwargs={"application_pk": application_pk}),
        )

        main_form = EditGMPForm(data=model_to_dict(application), instance=application)

        create_page_errors(main_form, page_errors)
        errors.add(page_errors)

        if main_form.is_valid():
            _check_certificate_errors(application, errors)
            _check_brand_errors(application, errors)

        errors.add(get_org_update_request_errors(application, "export"))

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
            "case_type": "export",
        }

        return render(request, "web/domains/case/export/submit-gmp.html", context)


def _check_certificate_errors(
    application: CertificateOfGoodManufacturingPracticeApplication, errors: ApplicationErrors
) -> None:
    if application.gmp_certificate_issued == application.CertificateTypes.ISO_22716:
        _add_cert_error(application, errors, GMPFile.Type.ISO_22716)  # type: ignore[arg-type]

        if application.auditor_accredited == YesNoChoices.yes:
            _add_cert_error(application, errors, GMPFile.Type.ISO_17021)  # type: ignore[arg-type]

        if application.auditor_certified == YesNoChoices.yes:
            _add_cert_error(application, errors, GMPFile.Type.ISO_17065)  # type: ignore[arg-type]

    elif application.gmp_certificate_issued == application.CertificateTypes.BRC_GSOCP:
        _add_cert_error(application, errors, GMPFile.Type.BRC_GSOCP)  # type: ignore[arg-type]


def _add_cert_error(
    application: CertificateOfGoodManufacturingPracticeApplication,
    errors: ApplicationErrors,
    file_type: GMPFile.Type,
) -> None:
    application_files = GMPFile.objects.filter(
        certificateofgoodmanufacturingpracticeapplication=application, is_active=True
    )
    if not application_files.filter(file_type=file_type).exists():
        cert_page_errors = PageErrors(
            page_name=f"{file_type.label} Certificate",
            url=reverse(
                "export:gmp-add-document",
                kwargs={"application_pk": application.pk, "file_type": file_type.value},
            ),
        )

        cert_page_errors.add(
            FieldError(
                field_name=f"{file_type.label} Certificate",
                messages=[f"You must upload an {file_type.label} certificate."],
            )
        )

        errors.add(cert_page_errors)


@login_required
def gmp_add_brand(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfGoodManufacturingPracticeApplication = get_object_or_404(
            CertificateOfGoodManufacturingPracticeApplication.objects.select_for_update(),
            pk=application_pk,
        )

        check_application_permission(application, request.user, "export")

        task = get_application_current_task(application, "export", "prepare")

        if request.POST:
            form = GMPBrandForm(data=request.POST)

            if form.is_valid():
                brand = form.save()
                application.brands.add(brand)

                return redirect(
                    reverse("export:gmp-edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = GMPBrandForm()

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Add brand",
            "case_type": "export",
        }

        return render(request, "web/domains/case/export/gmp-edit-brand.html", context)


@login_required
def gmp_edit_brand(
    request: AuthenticatedHttpRequest, *, application_pk: int, brand_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfGoodManufacturingPracticeApplication = get_object_or_404(
            CertificateOfGoodManufacturingPracticeApplication.objects.select_for_update(),
            pk=application_pk,
        )

        check_application_permission(application, request.user, "export")

        task = get_application_current_task(application, "export", "prepare")

        instance = application.brands.filter(pk=brand_pk).first()

        if not instance:
            return redirect(reverse("export:gmp-edit", kwargs={"application_pk": application_pk}))

        if request.POST:
            form = GMPBrandForm(instance=instance, data=request.POST)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("export:gmp-edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = GMPBrandForm(instance=instance)

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "instance": instance,
            "page_title": "Edit brand",
            "case_type": "export",
        }

        return render(request, "web/domains/case/export/gmp-edit-brand.html", context)


@require_POST
@login_required
def gmp_delete_brand(
    request: AuthenticatedHttpRequest, *, application_pk: int, brand_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfGoodManufacturingPracticeApplication = get_object_or_404(
            CertificateOfGoodManufacturingPracticeApplication.objects.select_for_update(),
            pk=application_pk,
        )

        check_application_permission(application, request.user, "export")

        instance = application.brands.filter(pk=brand_pk).first()

        if instance:
            application.brands.remove(instance)

        return redirect(reverse("export:gmp-edit", kwargs={"application_pk": application_pk}))


def _check_brand_errors(
    application: CertificateOfGoodManufacturingPracticeApplication,
    errors: ApplicationErrors,
) -> None:
    if not application.brands.exists():
        brand_page_errors = PageErrors(
            page_name="Brands",
            url=reverse(
                "export:gmp-add-brand",
                kwargs={"application_pk": application.pk},
            ),
        )

        brand_page_errors.add(
            FieldError(field_name="Brands", messages=["At least one brand name must be added"])
        )

        errors.add(brand_page_errors)
