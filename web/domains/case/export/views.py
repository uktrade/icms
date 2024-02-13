from typing import NamedTuple

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView
from django_ratelimit import UNSAFE
from django_ratelimit.decorators import ratelimit
from guardian.shortcuts import get_objects_for_user

from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.services import case_progress, document_pack
from web.domains.case.utils import (
    get_application_form,
    redirect_after_submit,
    submit_application,
    view_application_file,
)
from web.domains.file.utils import create_file_model
from web.flow.models import ProcessTypes
from web.models import (
    CertificateApplicationTemplate,
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    CFSProduct,
    CFSProductActiveIngredient,
    CFSProductType,
    CFSSchedule,
    ExportApplication,
    ExportApplicationType,
    Exporter,
    GMPFile,
    ProductLegislation,
    Task,
    User,
)
from web.models.shared import AddressEntryType, YesNoChoices
from web.permissions import AppChecker, Perms
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
    EditCOMForm,
    EditGMPForm,
    ProductsFileUploadForm,
    SubmitCFSScheduleForm,
    SubmitCOMForm,
    SubmitGMPForm,
    form_class_for_application_type,
)
from .utils import CustomError, generate_product_template_xlsx, process_products_file


def check_can_edit_application(
    user: User,
    application: (
        CertificateOfFreeSaleApplication
        | CertificateOfGoodManufacturingPracticeApplication
        | CertificateOfManufactureApplication
    ),
) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


def _get_active_application_types() -> dict[str, QuerySet]:
    return {
        "application_types": ExportApplicationType.objects.filter(is_active=True).order_by(
            "type_code"
        )
    }


class ExportApplicationChoiceView(PermissionRequiredMixin, TemplateView):
    template_name = "web/domains/case/export/choose.html"
    permission_required = Perms.sys.exporter_access

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context | _get_active_application_types()


class CreateExportApplicationConfig(NamedTuple):
    model_class: type[ExportApplication]
    form_class: type[CreateExportApplicationForm]
    certificate_message: str


@login_required
@permission_required(Perms.sys.exporter_access, raise_exception=True)
@ratelimit(key="ip", rate="5/m", block=True, method=UNSAFE)
def create_export_application(
    request: AuthenticatedHttpRequest, *, type_code: str, template_pk: int | None = None
) -> HttpResponse:
    """Create a certificate application.

    Supports setting application data from an optional template.

    :param request: Request
    :param type_code: Type of application to create.
    :param template_pk: Optional PK of a template to populate application
    """
    app_template: CertificateApplicationTemplate | None
    application_type: ExportApplicationType = ExportApplicationType.objects.get(type_code=type_code)

    if not application_type.is_active:
        raise ValueError(f"Export application of type {application_type.type_code} is not active")

    config = _get_export_app_config(type_code)

    if template_pk:
        try:
            app_template = get_application_template(request.user, template_pk)
        except PermissionDenied:
            # User cannot use this template, so redirect to the regular form.
            return redirect("export:create-application", type_code=type_code.lower())
        else:
            if not app_template.is_active:
                messages.info(request, "Cannot create an application from an archived template.")
                return redirect("export:create-application", type_code=type_code.lower())
    else:
        app_template = None

    if request.method == "POST":
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
            application.application_type = application_type

            with transaction.atomic():
                application.save()

                if app_template:
                    # Set template data and save
                    set_template_data(application, app_template, type_code)

                    # Refresh in case any template data has been saved.
                    application.refresh_from_db()

                Task.objects.create(
                    process=application, task_type=Task.TaskType.PREPARE, owner=request.user
                )

                # GMP applications are for China only
                if application_type.type_code == ExportApplicationType.Types.GMP:
                    country = application_type.country_group.countries.filter(
                        is_active=True
                    ).first()
                    application.countries.add(country)

                elif application_type.type_code == ExportApplicationType.Types.FREE_SALE:
                    application.schedules.create(created_by=request.user)

                # Add a draft certificate when creating an application
                # Ensures we never have to check for None
                document_pack.pack_draft_create(application)

            return redirect(
                reverse(application.get_edit_view_name(), kwargs={"application_pk": application.pk})
            )

    else:
        form = config.form_class(user=request.user)

    exporters_with_agents = get_objects_for_user(
        request.user, [Perms.obj.exporter.is_agent], Exporter
    ).values_list("pk", flat=True)

    context = {
        "form": form,
        "export_application_type": application_type,
        "certificate_message": config.certificate_message,
        "application_title": ProcessTypes(config.model_class.PROCESS_TYPE).label,
        "exporters_with_agents": list(exporters_with_agents),
        "case_type": "export",
        "application_template": app_template,
    } | _get_active_application_types()

    return render(request, "web/domains/case/export/create.html", context)


def get_application_template(user: User, template_pk: int) -> CertificateApplicationTemplate:
    """Returns an application template if the user has access to it.

    :param user: User requesting the template.
    :param template_pk: Application template pk.
    """
    template = get_object_or_404(CertificateApplicationTemplate, pk=template_pk)

    if template.user_can_view(user):
        return template
    else:
        raise PermissionDenied


def set_template_data(
    application: ExportApplication,
    template: CertificateApplicationTemplate,
    type_code: str,
) -> None:
    """Update the supplied application with the template data provided.

    :param application: Export Application
    :param template: Application Template
    :param type_code: App type.
    """
    form_class = form_class_for_application_type(type_code)
    form = form_class(instance=application, data=template.form_data())

    if form.is_valid():
        form.save()


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
                "If you are supplying the product to a client in the UK then you do not require a certificate."
                " Your client may need to apply for a certificate if they subsequently export"
                " it to one of their clients outside of the UK."
                "\n\nDIT does not issue Certificates of Free sale for food, drinks, supplements, CE marked"
                " medical devices or pesticides. If you require a certificate for pesticides, please"
                " submit a Certificate of Manufacture application."
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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        form = get_application_form(application, request, EditCOMForm, SubmitCOMForm)

        if request.method == "POST":
            if form.is_valid():
                form.save()
                messages.success(request, "Application data saved")

                return redirect(
                    reverse("export:com-edit", kwargs={"application_pk": application_pk})
                )

        context = {
            "process": application,
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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)
        task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)

        errors = ApplicationErrors()

        edit_url = reverse("export:com-edit", kwargs={"application_pk": application_pk})
        edit_url = f"{edit_url}?validate"

        page_errors = PageErrors(page_name="Application details", url=edit_url)
        create_page_errors(
            SubmitCOMForm(data=model_to_dict(application), instance=application), page_errors
        )
        errors.add(page_errors)

        errors.add(get_org_update_request_errors(application, "export"))

        if request.method == "POST":
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                submit_application(application, request, task)

                return redirect_after_submit(application, request)

        else:
            form = SubmitForm()

        context = {
            "process": application,
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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        if request.method == "POST":
            form = EditCFSForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("export:cfs-edit", kwargs={"application_pk": application_pk})
                )

        else:
            initial = {} if application.contact else {"contact": request.user}
            form = EditCFSForm(instance=application, initial=initial)

        schedules = application.schedules.all().order_by("created_at")

        context = {
            "process": application,
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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        new_schedule = CFSSchedule.objects.create(application=application, created_by=request.user)

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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        if request.method == "POST":
            form = EditCFScheduleForm(data=request.POST, instance=schedule)

            if form.is_valid():
                form.save()
                messages.success(request, "Schedule data saved")

                return redirect(
                    reverse(
                        "export:cfs-schedule-edit",
                        kwargs={"application_pk": application_pk, "schedule_pk": schedule.pk},
                    )
                )

        else:
            form_kwargs = {"instance": schedule}

            # query param to fully validate the form.
            if "validate" in request.GET:
                form_kwargs["data"] = model_to_dict(schedule)
                form = SubmitCFSScheduleForm(**form_kwargs)
            else:
                form = EditCFScheduleForm(**form_kwargs)

        schedule_legislations = schedule.legislations.filter(is_active=True)

        has_cosmetics = schedule_legislations.filter(is_eu_cosmetics_regulation=True).exists()
        not_export_only = schedule.goods_export_only == YesNoChoices.no
        show_schedule_statements_is_responsible_person = has_cosmetics and not_export_only

        legislation_config = {
            legislation.pk: {"isEUCosmeticsRegulation": legislation.is_eu_cosmetics_regulation}
            for legislation in ProductLegislation.objects.filter(is_active=True)
        }

        context = {
            "process": application,
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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        schedule: CFSSchedule = application.schedules.get(pk=schedule_pk)
        schedule.delete()

        return redirect(reverse("export:cfs-edit", kwargs={"application_pk": application_pk}))


@login_required
def cfs_set_manufacturer(
    request: AuthenticatedHttpRequest, *, application_pk: int, schedule_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        if request.method == "POST":
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
            "process": application,
            "schedule": schedule,
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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        schedule.manufacturer_name = None
        schedule.manufacturer_address_entry_type = AddressEntryType.MANUAL
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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        if request.method == "POST":
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
            "process": application,
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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        product: CFSProduct = get_object_or_404(
            schedule.products.select_for_update(), pk=product_pk
        )

        if request.method == "POST":
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
            "process": application,
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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        product: CFSProduct = get_object_or_404(
            schedule.products.select_for_update(), pk=product_pk
        )

        if request.method == "POST":
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
            "process": application,
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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        product: CFSProduct = get_object_or_404(
            schedule.products.select_for_update(), pk=product_pk
        )

        ingredient: CFSProductActiveIngredient = get_object_or_404(
            product.active_ingredients.select_for_update(), pk=ingredient_pk
        )

        if request.method == "POST":
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
            "process": application,
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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        product: CFSProduct = get_object_or_404(
            schedule.products.select_for_update(), pk=product_pk
        )

        if request.method == "POST":
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
            "process": application,
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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        schedule: CFSSchedule = get_object_or_404(
            CFSSchedule.objects.select_for_update(), pk=schedule_pk
        )

        product: CFSProduct = get_object_or_404(
            schedule.products.select_for_update(), pk=product_pk
        )

        product_type: CFSProductType = get_object_or_404(
            product.product_type_numbers.select_for_update(), pk=product_type_pk
        )

        if request.method == "POST":
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
            "process": application,
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
    with transaction.atomic():
        application: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

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
            check_can_edit_application(request.user, application)

            case_progress.application_in_progress(application)

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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        schedule_to_copy: CFSSchedule = get_object_or_404(application.schedules, pk=schedule_pk)

        # ManyToMany you can just use `.all()` to get the records
        # ForeignKeys you have to fetch from the db before the save.
        legislations_to_copy = schedule_to_copy.legislations.all()
        products_to_copy = [p for p in schedule_to_copy.products.all().order_by("pk")]

        schedule_to_copy.pk = None
        schedule_to_copy._state.adding = True
        schedule_to_copy.created_by = request.user
        schedule_to_copy.save()

        # Copy the legislation records
        schedule_to_copy.legislations.set(legislations_to_copy)

        # copy the product records
        for product in products_to_copy:
            product_types_to_copy = [pt for pt in product.product_type_numbers.all().order_by("pk")]
            ingredients_to_copy = [i for i in product.active_ingredients.all().order_by("pk")]

            product.pk = None
            product._state.adding = True
            product.schedule = schedule_to_copy
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

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)
        task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)

        errors = _get_cfs_errors(application)

        if request.method == "POST":
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                submit_application(application, request, task)

                return redirect_after_submit(application, request)

        else:
            form = SubmitForm()

        context = {
            "process": application,
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
    schedules = application.schedules.all().order_by("created_at")

    if not schedules.exists():
        page_errors.add(
            FieldError(field_name="Schedule", messages=["At least one schedule must be added"])
        )

    else:
        for idx, schedule in enumerate(schedules, start=1):
            edit_schedule_url = reverse(
                "export:cfs-schedule-edit",
                kwargs={"application_pk": application.pk, "schedule_pk": schedule.pk},
            )
            edit_schedule_url = f"{edit_schedule_url}?validate"

            schedule_page_errors = PageErrors(page_name=f"Schedule {idx}", url=edit_schedule_url)
            create_page_errors(
                SubmitCFSScheduleForm(data=model_to_dict(schedule), instance=schedule),
                schedule_page_errors,
            )

            errors.add(schedule_page_errors)

            # Check that the schedule has products if legislation has been set
            schedule_legislations = schedule.legislations.filter(is_active=True)
            if schedule_legislations.exists() and not schedule.products.exists():
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

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        form = get_application_form(application, request, EditGMPForm, SubmitGMPForm)

        if request.method == "POST":
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
                messages.success(request, "Application data saved")

                return redirect(
                    reverse("export:gmp-edit", kwargs={"application_pk": application_pk})
                )

        form_valid = SubmitGMPForm(data=model_to_dict(application), instance=application).is_valid()
        show_iso_table = (
            form_valid
            and application.gmp_certificate_issued == application.CertificateTypes.ISO_22716
        )
        show_brc_table = (
            form_valid
            and application.gmp_certificate_issued == application.CertificateTypes.BRC_GSOCP
        )

        context = {
            "process": application,
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

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        if request.method == "POST":
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
            "process": application,
            "form": form,
            "page_title": "Certificate of Good Manufacturing Practice - Add supporting document",
            "page_subtitle": f"Add {GMPFile.Type[file_type].label} document",
            "prev_link": prev_link,
            "case_type": "export",
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
        request.user, application, application.supporting_documents, document_pk
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

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

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
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)
        task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)

        errors = ApplicationErrors()

        edit_url = reverse("export:gmp-edit", kwargs={"application_pk": application_pk})
        edit_url = f"{edit_url}?validate"

        page_errors = PageErrors(page_name="Application details", url=edit_url)
        main_form = SubmitGMPForm(data=model_to_dict(application), instance=application)

        create_page_errors(main_form, page_errors)
        errors.add(page_errors)

        if main_form.is_valid():
            _check_certificate_errors(application, errors)

        errors.add(get_org_update_request_errors(application, "export"))

        if request.method == "POST":
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                submit_application(application, request, task)

                return redirect_after_submit(application, request)

        else:
            form = SubmitForm()

        context = {
            "process": application,
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
        _add_cert_error(application, errors, GMPFile.Type.ISO_22716)

        if application.auditor_accredited == YesNoChoices.yes:
            _add_cert_error(application, errors, GMPFile.Type.ISO_17021)

        if application.auditor_certified == YesNoChoices.yes:
            _add_cert_error(application, errors, GMPFile.Type.ISO_17065)

    elif application.gmp_certificate_issued == application.CertificateTypes.BRC_GSOCP:
        _add_cert_error(application, errors, GMPFile.Type.BRC_GSOCP)


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
