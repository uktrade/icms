from django.db.models import Q, QuerySet

from web.domains.exporter.models import Exporter
from web.models import (
    CertificateApplicationTemplate,
    CertificateOfFreeSaleApplicationTemplate,
    CertificateOfGoodManufacturingPracticeApplicationTemplate,
    CertificateOfManufactureApplicationTemplate,
    ExportApplicationType,
    User,
)
from web.permissions import get_user_exporter_permissions, organisation_get_contacts

from .forms import CreateCATForm


def create_cat(
    form: CreateCATForm, owner: User, create_cfs_schedule: bool = True
) -> CertificateApplicationTemplate:
    cat: CertificateApplicationTemplate = form.save(commit=False)
    cat.owner = owner
    cat.save()

    match cat.application_type:
        case ExportApplicationType.Types.FREE_SALE:
            template_cls = CertificateOfFreeSaleApplicationTemplate

        case ExportApplicationType.Types.MANUFACTURE:
            template_cls = CertificateOfManufactureApplicationTemplate

        case ExportApplicationType.Types.GMP:
            template_cls = CertificateOfGoodManufacturingPracticeApplicationTemplate

        case _:
            raise ValueError(f"Unknown application type {cat.application_type}")

    template_cls.objects.create(template=cat)

    if cat.application_type == ExportApplicationType.Types.FREE_SALE and create_cfs_schedule:
        cat.refresh_from_db()
        cat.cfs_template.schedules.create(created_by=owner)

    return cat


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

    return cats.order_by("-created_datetime")


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
