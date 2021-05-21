from typing import Type, Union

import django.forms as django_forms
import weasyprint
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from web.flow.models import Task
from web.utils.s3 import get_file_from_s3

from . import forms
from .derogations.models import DerogationsApplication
from .fa_dfl.models import DFLApplication
from .fa_oil.models import OpenIndividualLicenceApplication
from .fa_sil.models import SILApplication
from .forms import ImportContactLegalEntityForm, ImportContactPersonForm
from .models import ImportApplication, ImportApplicationType, ImportContact
from .sanctions.models import SanctionsAndAdhocApplication
from .wood.models import WoodQuotaApplication


class ImportApplicationChoiceView(PermissionRequiredMixin, TemplateView):
    template_name = "web/domains/case/import/choose.html"
    permission_required = "web.importer_access"


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_derogations(request: HttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.Types.DEROGATION
    model_class = DerogationsApplication
    redirect_view = "import:derogations:edit-derogations"

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
        redirect_view,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_sanctions(request: HttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.Types.SANCTION_ADHOC
    model_class = SanctionsAndAdhocApplication
    redirect_view = "import:sanctions:edit-application"

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
        redirect_view,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_firearms_oil(request: HttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.SubTypes.OIL
    model_class = OpenIndividualLicenceApplication
    redirect_view = "import:fa-oil:edit-oil"

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
        redirect_view,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_firearms_dfl(request: HttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.SubTypes.DFL
    model_class = DFLApplication
    redirect_view = "import:fa-dfl:edit"

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
        redirect_view,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_firearms_sil(request: HttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.SubTypes.SIL
    model_class = SILApplication
    redirect_view = "import:fa-sil:edit"
    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
        redirect_view,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_wood_quota(request: HttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.Types.WOOD_QUOTA
    model_class = WoodQuotaApplication
    redirect_view = "import:wood:edit-quota"

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
        redirect_view,
        form_class=forms.CreateWoodQuotaApplicationForm,
    )


def _create_application(
    request: HttpRequest,
    import_application_type: Union[ImportApplicationType.Types, ImportApplicationType.SubTypes],
    model_class: Type[ImportApplication],
    redirect_view: str,
    form_class: Type[forms.CreateImportApplicationForm] = None,
) -> HttpResponse:
    """Helper function to create one of several types of importer application.

    :param request: Django request
    :param import_application_type: ImportApplicationType type or sub_type
    :param model_class: ImportApplication class
    :param redirect_view: View to redirect to
    :param form_class: Optional form class that defines extra logic
    :return:
    """

    application_type: ImportApplicationType = ImportApplicationType.objects.get(
        Q(type=import_application_type) | Q(sub_type=import_application_type)
    )

    if form_class is None:
        form_class = forms.CreateImportApplicationForm

    if request.POST:
        form = form_class(request.POST, user=request.user)

        if form.is_valid():
            application = model_class()
            application.importer = form.cleaned_data["importer"]
            application.importer_office = form.cleaned_data["importer_office"]
            application.process_type = model_class.PROCESS_TYPE
            application.created_by = request.user
            application.last_updated_by = request.user
            application.submitted_by = request.user
            application.application_type = application_type

            with transaction.atomic():
                application.save()
                Task.objects.create(process=application, task_type="prepare", owner=request.user)

            return redirect(reverse(redirect_view, kwargs={"pk": application.pk}))
    else:
        form = form_class(user=request.user)

    context = {"form": form, "import_application_type": application_type}

    return render(request, "web/domains/case/import/create.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_cover_letter(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        if request.POST:
            form = forms.CoverLetterForm(request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )
        else:
            form = forms.CoverLetterForm(instance=application)

        context = {
            "case_type": "import",
            "process": application,
            "task": task,
            "page_title": "Cover Letter Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/edit-cover-letter.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_licence(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        if request.POST:
            form = forms.LicenceDateForm(request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )
        else:
            form = forms.LicenceDateForm(instance=application)

        context = {
            "case_type": "import",
            "process": application,
            "task": task,
            "page_title": "Licence Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/edit-licence.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def add_endorsement(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    return _add_endorsement(request, application_pk, forms.EndorsementChoiceImportApplicationForm)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def add_custom_endorsement(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    return _add_endorsement(request, application_pk, forms.EndorsementImportApplicationForm)


def _add_endorsement(
    request: HttpRequest, application_pk: int, Form: Type[django_forms.ModelForm]
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        if request.POST:
            form = Form(request.POST)

            if form.is_valid():
                endorsement = form.save(commit=False)
                endorsement.import_application = application
                endorsement.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )
        else:
            form = Form()

        context = {
            "case_type": "import",
            "process": application,
            "task": task,
            "page_title": "Endorsement Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/add-endorsement.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_endorsement(
    request: HttpRequest, *, application_pk: int, endorsement_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        endorsement = get_object_or_404(application.endorsements, pk=endorsement_pk)
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        if request.POST:
            form = forms.EndorsementImportApplicationForm(request.POST, instance=endorsement)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )
        else:
            form = forms.EndorsementImportApplicationForm(instance=endorsement)

        context = {
            "case_type": "import",
            "process": application,
            "task": task,
            "page_title": "Endorsement Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/edit-endorsement.html",
            context=context,
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
@require_POST
def delete_endorsement(
    request: HttpRequest, *, application_pk: int, endorsement_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        endorsement = get_object_or_404(application.endorsements, pk=endorsement_pk)
        application.get_task([ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        endorsement.delete()

        return redirect(
            reverse(
                "case:prepare-response",
                kwargs={"application_pk": application_pk, "case_type": "import"},
            )
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_GET
def preview_cover_letter(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        context = {
            "process": application,
            "task": task,
            "page_title": "Cover Letter Preview",
            "issue_date": application.licence_issue_date.strftime("%d %B %Y"),
            "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        }

        html_string = render_to_string(
            request=request,
            template_name="web/domains/case/import/manage/preview-cover-letter.html",
            context=context,
        )

        html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf_file = html.write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = "filename=CoverLetter.pdf"

        return response


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_GET
def preview_licence(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        context = {
            "process": application,
            "task": task,
            "page_title": "Licence Preview",
            "issue_date": application.licence_issue_date.strftime("%d %B %Y"),
        }

        # TODO: preview-licence.html contents are hard-coded and seem to be for
        # a specific type of firearms application. needs to be generalized for
        # other application types.
        html_string = render_to_string(
            request=request,
            template_name="web/domains/case/import/manage/preview-licence.html",
            context=context,
        )

        html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf_file = html.write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = "filename=Licence.pdf"
        return response


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def authorisation(request, application_pk):
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        application_errors = []
        if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
            if not application.openindividuallicenceapplication.checklists.exists():
                url = reverse("import:fa-oil:manage-checklist", args=[application.pk])
                html = f"<a href='{url}'>Please complete checklist.</a>"
                application_errors.append(html)

        if application.decision == ImportApplication.REFUSE:
            url = reverse(
                "case:prepare-response",
                kwargs={"application_pk": application.pk, "case_type": "import"},
            )
            html = f"<a href='{url}'>Please approve application.</a>"
            application_errors.append(html)

        if not application.licence_start_date or not application.licence_end_date:
            url = reverse(
                "case:prepare-response",
                kwargs={"application_pk": application.pk, "case_type": "import"},
            )
            html = f"<a href='{url}'>Please complete start and end dates.</a>"
            application_errors.append(html)

        context = {
            "case_type": "import",
            "process": application,
            "task": task,
            "page_title": "Authorisation",
            "application_errors": application_errors,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/authorisation.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def start_authorisation(request, application_pk):
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application.get_task([ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process")

        application.status = ImportApplication.PROCESSING
        application.save()

        return redirect(reverse("workbasket"))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def cancel_authorisation(request, application_pk):
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application.get_task(ImportApplication.PROCESSING, "process")

        application.status = ImportApplication.SUBMITTED
        application.save()

        return redirect(reverse("workbasket"))


# TODO: This can be replaced by the following:
# icms/web/domains/case/views.py -> def view_application_file
def view_file(request, application, related_file_model, file_pk):
    has_perm_importer = request.user.has_perm("web.importer_access")
    has_perm_reference_data = request.user.has_perm("web.reference_data_access")

    if not has_perm_importer and not has_perm_reference_data:
        raise PermissionDenied

    # first check is for case managers (who are not marked as contacts of
    # importers), second is for people submitting applications
    if not has_perm_reference_data and not request.user.has_perm(
        "web.is_contact_of_importer", application.importer
    ):
        raise PermissionDenied

    document = related_file_model.get(pk=file_pk)
    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


# TODO: Revisit these if we get around to ICMSLST-657
@login_required
@permission_required("web.importer_access", raise_exception=True)
def list_import_contacts(request: HttpRequest, pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "contacts": application.importcontact_set.all(),
            "page_title": "Firearms & Ammunition - Contacts",
        }

        return render(request, "web/domains/case/import/fa-import-contacts/list.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_import_contact(request: HttpRequest, pk: int, entity: str) -> HttpResponse:
    form_class = _get_entity_form(entity)

    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = form_class(data=request.POST, files=request.FILES)

            if form.is_valid():
                import_contact = form.save(commit=False)
                import_contact.import_application = application
                import_contact.entity = entity
                import_contact.save()

                # Assume known_bought_from is True if we are adding an import contact
                _update_know_bought_from(application)

                return redirect(
                    reverse(
                        "import:fa-edit-import-contact",
                        kwargs={
                            "application_pk": pk,
                            "entity": entity,
                            "contact_pk": import_contact.pk,
                        },
                    )
                )
        else:
            form = form_class()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Open Individual Import Licence",
        }

        return render(request, "web/domains/case/import/fa-import-contacts/create.html", context)


def _update_know_bought_from(application: ImportApplication) -> None:
    # Map process types to the ImportApplication link to that class
    process_type_link = {
        OpenIndividualLicenceApplication.PROCESS_TYPE: "openindividuallicenceapplication",
        DFLApplication.PROCESS_TYPE: "dflapplication",
    }

    supported_types = Union[OpenIndividualLicenceApplication, DFLApplication]

    try:
        link = process_type_link[application.process_type]
    except KeyError:
        raise NotImplementedError(
            f"Unable to check know_bought_from: Unknown Firearm process_type: {application.process_type}"
        )

    # e.g. application.openindividuallicenceapplication to get access to OpenIndividualLicenceApplication
    firearms_application: supported_types = getattr(application, link)

    if not firearms_application.know_bought_from:
        firearms_application.know_bought_from = True
        firearms_application.save()


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_import_contact(
    request: HttpRequest, application_pk: int, entity: str, contact_pk: int
) -> HttpResponse:

    form_class = _get_entity_form(entity)

    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        person = get_object_or_404(ImportContact, pk=contact_pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = form_class(data=request.POST, instance=person)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:fa-edit-import-contact",
                        kwargs={
                            "application_pk": application_pk,
                            "entity": entity,
                            "contact_pk": contact_pk,
                        },
                    )
                )

        else:
            form = form_class(instance=person)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Open Individual Import Licence - Edit Import Contact",
        }

        return render(request, "web/domains/case/import/fa-import-contacts/edit.html", context)


def _get_entity_form(
    entity: str,
) -> Type[Union[ImportContactLegalEntityForm, ImportContactPersonForm]]:

    if entity == ImportContact.LEGAL:
        form_class = ImportContactLegalEntityForm

    elif entity == ImportContact.NATURAL:
        form_class = ImportContactPersonForm

    else:
        raise NotImplementedError(f"View does not support entity type: {entity}")

    return form_class
