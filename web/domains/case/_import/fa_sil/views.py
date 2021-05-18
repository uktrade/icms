from typing import NamedTuple, Type, Union

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..models import ImportApplication
from . import forms, models

GoodsModel = Union[
    models.SILGoodsSection1,
    models.SILGoodsSection2,
    models.SILGoodsSection5,
    models.SILGoodsSection582Obsolete,
    models.SILGoodsSection582Other,
]
GoodsModelT = Type[GoodsModel]

GoodsForm = Union[
    forms.SILGoodsSection1Form,
    forms.SILGoodsSection2Form,
    forms.SILGoodsSection5Form,
    forms.SILGoodsSection582ObsoleteForm,
    forms.SILGoodsSection582OtherForm,
]
GoodsFormT = Type[GoodsForm]


class CreateSILSectionConfig(NamedTuple):
    model_class: GoodsModelT
    form_class: GoodsFormT
    template: str


def _get_sil_section_app_config(sil_section_type: str) -> CreateSILSectionConfig:
    if sil_section_type == "section1":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection1,
            form_class=forms.SILGoodsSection1Form,
            template="web/domains/case/import/fa-sil/goods/section1.html",
        )

    elif sil_section_type == "section2":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection2,
            form_class=forms.SILGoodsSection2Form,
            template="web/domains/case/import/fa-sil/goods/section2.html",
        )

    elif sil_section_type == "section5":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection5,
            form_class=forms.SILGoodsSection5Form,
            template="web/domains/case/import/fa-sil/goods/section5.html",
        )

    elif sil_section_type == "section582-obsolete":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection582Obsolete,
            form_class=forms.SILGoodsSection582ObsoleteForm,
            template="web/domains/case/import/fa-sil/goods/section582-obsolete.html",
        )

    elif sil_section_type == "section582-other":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection582Other,
            form_class=forms.SILGoodsSection582OtherForm,
            template="web/domains/case/import/fa-sil/goods/section582-other.html",
        )
    raise NotImplementedError(f"sil_section_type is not supported: {sil_section_type}")


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit(request: HttpRequest, pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(models.SILApplication.objects.select_for_update(), pk=pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = forms.PrepareSILForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(reverse("import:fa-sil:edit", kwargs={"pk": pk}))

        else:
            form = forms.PrepareSILForm(instance=application, initial={"contact": request.user})

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Edit",
        }

        return render(request, "web/domains/case/import/fa-sil/edit.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def choose_goods_section(request: HttpRequest, *, pk: int) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Edit Goods",
        }

        return render(request, "web/domains/case/import/fa-sil/choose-goods-section.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def add_section(request: HttpRequest, application_pk: int, sil_section_type: str) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        config = _get_sil_section_app_config(sil_section_type)

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = config.form_class(request.POST)
            if form.is_valid():
                goods = form.save(commit=False)
                goods.import_application = application
                goods.save()
                return redirect(reverse("import:fa-sil:edit", kwargs={"pk": application.pk}))
        else:
            form = config.form_class()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Add Goods",
        }

        return render(request, config.template, context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_section(
    request: HttpRequest,
    application_pk: int,
    sil_section_type: str,
    section_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        config = _get_sil_section_app_config(sil_section_type)
        goods: GoodsModel = get_object_or_404(config.model_class, pk=section_pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = config.form_class(request.POST, instance=goods)
            if form.is_valid():
                goods = form.save(commit=False)
                goods.import_application = application
        else:
            form = config.form_class(instance=goods)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Edit Goods",
        }

        return render(request, config.template, context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
@require_POST
def delete_section(
    request: HttpRequest, application_pk: int, sil_section_type: str, section_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        config = _get_sil_section_app_config(sil_section_type)
        goods: GoodsModel = get_object_or_404(config.model_class, pk=section_pk)

        application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        goods.is_active = False
        goods.save()

        return redirect(reverse("import:fa-sil:edit", kwargs={"pk": application_pk}))
