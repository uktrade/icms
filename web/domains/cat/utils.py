from typing import Any

from django.db.models import Q, QuerySet
from django.forms import ModelForm, model_to_dict

from web.domains.case.export.forms import (
    CFSManufacturerDetailsForm,
    EditCFScheduleForm,
    EditCFSForm,
    EditCOMForm,
    EditGMPForm,
)
from web.domains.exporter.models import Exporter
from web.models import (
    CertificateApplicationTemplate,
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    CFSScheduleTemplate,
    ExportApplicationType,
    User,
)
from web.permissions import get_user_exporter_permissions, organisation_get_contacts
from web.utils.sentry import capture_message


class InvalidTemplateException(Exception): ...  # noqa: E701


def set_template_data(
    application: (
        CertificateOfFreeSaleApplication
        | CertificateOfManufactureApplication
        | CertificateOfGoodManufacturingPracticeApplication
    ),
    template: CertificateApplicationTemplate,
    user: User,
) -> None:
    """Update the supplied application with the template data provided.

    :param application: Export Application
    :param template: Application Template
    :param user: User who is creating the template.
    """

    if template.application_type == ExportApplicationType.Types.MANUFACTURE:
        template_data = template.com_template
        form_cls = EditCOMForm
    elif template.application_type == ExportApplicationType.Types.GMP:
        template_data = template.gmp_template
        form_cls = EditGMPForm
    elif template.application_type == ExportApplicationType.Types.FREE_SALE:
        template_data = template.cfs_template
        form_cls = EditCFSForm
    else:
        raise ValueError(f"Unable to create template for app type: {template.application_type}")

    # Get data that we can save in the real application
    data = model_to_dict(template_data, exclude=["id", "template"])
    form = form_cls(instance=application, data=data)

    cat_pk = template.pk
    _save_form(form, cat_pk)

    # Extra CFS steps
    if template.application_type == ExportApplicationType.Types.FREE_SALE:
        schedules_to_copy: QuerySet[CFSScheduleTemplate] = template_data.schedules.all()

        for schedule_template in schedules_to_copy:
            # Create an empty schedule before saving template data using form.
            instance = application.schedules.create(created_by=user)
            data = model_to_dict(schedule_template, exclude=["id", "application"])
            form = EditCFScheduleForm(instance=instance, data=data)
            new_schedule: CFSScheduleTemplate = _save_form(form, cat_pk)

            # Copy the legislation records
            new_schedule.legislations.set(schedule_template.legislations.all())

            # Set the manufacturer data.
            if data.get("manufacturer_name"):
                form = CFSManufacturerDetailsForm(instance=new_schedule, data=data)
                _save_form(form, cat_pk)

            # TODO: ICMSLST-2564 Add product data when creating application from template.
            # products_to_copy: list[CFSProductTemplate] = [p for p in schedule_template.products.all().order_by("pk")]
            # for product in products_to_copy:
            #     product_types_to_copy = [pt for pt in product.product_type_numbers.all().order_by("pk")]
            #     ingredients_to_copy = [i for i in product.active_ingredients.all().order_by("pk")]
            #
            #     product.pk = None
            #     product._state.adding = True
            #     product.schedule = new_schedule
            #     product.save()
            #
            #     for ptn in product_types_to_copy:
            #         ptn.pk = None
            #         ptn._state.adding = True
            #         ptn.product = product
            #         ptn.save()
            #
            #     for ingredient in ingredients_to_copy:
            #         ingredient.pk = None
            #         ingredient._state.adding = True
            #         ingredient.product = product
            #         ingredient.save()


def _save_form(form: ModelForm, cat_pk: int) -> Any:
    if form.is_valid():
        return form.save()
    else:
        error_msg = f"Error creating template using CertificateApplicationTemplate(id={cat_pk}). Form errors: {form.errors.as_text()}"

        capture_message(error_msg)
        raise InvalidTemplateException(error_msg)


def get_user_templates(
    user: User, *, include_inactive: bool = False
) -> QuerySet[CertificateApplicationTemplate]:
    """Get CertificateApplicationTemplate records the user can see.

    Returns templates the user has created or templates created by contacts of exporters
    the user is associated with.
    """

    # Fetch exporters the user has any permissions at:
    exporter_permissions = get_user_exporter_permissions(user)
    exporters = Exporter.objects.filter(
        pk__in=[eop.content_object_id for eop in exporter_permissions]
    )

    # get a list of users at each exporter
    unique_contacts = set()
    for exporter in exporters:
        org_contacts = organisation_get_contacts(exporter).values_list("pk", flat=True)
        unique_contacts.update(set(org_contacts))

    extra_filter = {} if include_inactive else {"is_active": True}

    # Filter Templates by user pk list.
    cats = CertificateApplicationTemplate.objects.filter(
        # Templates shared by related contacts
        Q(
            owner_id__in=list(unique_contacts),
            sharing__in=[
                CertificateApplicationTemplate.SharingStatuses.VIEW,
                CertificateApplicationTemplate.SharingStatuses.EDIT,
            ],
        )
        # Templates the supplied user has created.
        | Q(owner=user),
        **extra_filter,
    )

    return cats


def template_in_user_templates(
    user: User, template: CertificateApplicationTemplate, *, include_inactive: bool = False
) -> bool:
    """Returns True if the supplied template exists in the templates linked to the user."""

    return (
        get_user_templates(user, include_inactive=include_inactive).filter(pk=template.pk).exists()
    )


def user_can_edit_template(user: User, template: CertificateApplicationTemplate) -> bool:
    """Returns True if the user can edit a template.

    NOTE: This does not check if the template exists in the user linked templates.
    """

    return (
        template.owner == user
        or template.sharing == CertificateApplicationTemplate.SharingStatuses.EDIT
    )
