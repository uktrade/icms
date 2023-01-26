from typing import Any

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from web.domains.case._import.textiles.models import TextilesApplication
from web.domains.case.export.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
)
from web.domains.case.services import document_pack
from web.models import (
    CertificateOfManufactureApplication,
    DerogationsApplication,
    DFLApplication,
    IronSteelApplication,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    PriorSurveillanceApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    WoodQuotaApplication,
)
from web.types import AuthenticatedHttpRequest
from web.utils.commodity import annotate_commodity_unit

from .. import forms
from ..types import ImpOrExp
from ..utils import get_case_page_title
from .utils import get_caseworker_view_readonly_status, get_class_imp_or_exp


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def prepare_response(
    request: AuthenticatedHttpRequest, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        if case_type == "import":
            if application.status == application.Statuses.VARIATION_REQUESTED:
                form_class = forms.ResponsePreparationVariationRequestImportForm
            else:
                form_class = forms.ResponsePreparationImportForm

        elif case_type == "export":
            form_class = forms.ResponsePreparationExportForm

        else:
            raise NotImplementedError(f"Unknown case_type {case_type}")

        readonly_view = get_caseworker_view_readonly_status(application, case_type, request.user)

        if request.method == "POST" and not readonly_view:
            form = form_class(request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": case_type},
                    )
                )
        else:
            form = form_class(instance=application)

        if case_type == "import":
            cover_letter_flag = application.application_type.cover_letter_flag
            electronic_licence_flag = application.application_type.electronic_licence_flag
            endorsements_flag = application.application_type.endorsements_flag
        else:
            cover_letter_flag = False
            electronic_licence_flag = False
            endorsements_flag = False

        context = {
            "case_type": case_type,
            "page_title": get_case_page_title(case_type, application, "Response Preparation"),
            "form": form,
            "cover_letter_flag": cover_letter_flag,
            "electronic_licence_flag": electronic_licence_flag,
            # Not used currently but the template probably should.
            # Once the data is confirmed to be correct
            "endorsements_flag": endorsements_flag,
            "readonly_view": readonly_view,
        }

    # Get the latest active licence if the variation is refused.
    if application.is_import_application():
        if (
            application.status == application.Statuses.VARIATION_REQUESTED
            and application.variation_decision == application.REFUSE
        ):
            context["licence"] = document_pack.pack_active_get(application)
            context["variation_refused"] = True

        else:
            # When an application is refused we don't show licence details
            if application.decision != application.REFUSE:
                context["licence"] = document_pack.pack_draft_get(application)

    # Import applications
    if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
        return _prepare_fa_oil_response(
            request, application.openindividuallicenceapplication, context  # type: ignore[union-attr]
        )

    elif application.process_type == DFLApplication.PROCESS_TYPE:
        return _prepare_fa_dfl_response(request, application.dflapplication, context)  # type: ignore[union-attr]

    elif application.process_type == SILApplication.PROCESS_TYPE:
        return _prepare_fa_sil_response(request, application.silapplication, context)  # type: ignore[union-attr]

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        return _prepare_sanctions_and_adhoc_response(
            request, application.sanctionsandadhocapplication, context  # type: ignore[union-attr]
        )

    elif application.process_type == DerogationsApplication.PROCESS_TYPE:
        return _prepare_derogations_response(request, application.derogationsapplication, context)  # type: ignore[union-attr]

    elif application.process_type == WoodQuotaApplication.PROCESS_TYPE:
        return _prepare_wood_quota_response(request, application.woodquotaapplication, context)  # type: ignore[union-attr]

    elif application.process_type == OutwardProcessingTradeApplication.PROCESS_TYPE:
        return _prepare_opt_response(
            request, application.outwardprocessingtradeapplication, context  # type: ignore[union-attr]
        )

    elif application.process_type == TextilesApplication.PROCESS_TYPE:
        return _prepare_textiles_quota_response(request, application.textilesapplication, context)  # type: ignore[union-attr]

    elif application.process_type == PriorSurveillanceApplication.PROCESS_TYPE:
        return _prepare_sps_response(request, application.priorsurveillanceapplication, context)  # type: ignore[union-attr]

    elif application.process_type == IronSteelApplication.PROCESS_TYPE:
        return _prepare_ironsteel_response(request, application.ironsteelapplication, context)  # type: ignore[union-attr]

    # Certificate applications
    elif application.process_type == CertificateOfManufactureApplication.PROCESS_TYPE:
        return _prepare_com_response(request, application.certificateofmanufactureapplication, context)  # type: ignore[union-attr]

    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        return _prepare_cfs_response(request, application.certificateoffreesaleapplication, context)  # type: ignore[union-attr]

    elif application.process_type == CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE:
        return _prepare_gmp_response(
            request, application.certificateofgoodmanufacturingpracticeapplication, context  # type: ignore[union-attr]
        )

    else:
        raise NotImplementedError(
            f"Application process type '{application.process_type}' haven't been configured yet"
        )


def _prepare_fa_oil_response(
    request: AuthenticatedHttpRequest,
    application: OpenIndividualLicenceApplication,
    context: dict[str, Any],
) -> HttpResponse:
    context.update({"process": application})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-fa-oil-response.html",
        context=context,
    )


def _prepare_fa_dfl_response(
    request: AuthenticatedHttpRequest, application: DFLApplication, context: dict[str, Any]
):
    context.update(
        {
            "process": application,
            "goods": application.goods_certificates.all().filter(is_active=True),
        }
    )

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-fa-dfl-response.html",
        context=context,
    )


def _prepare_fa_sil_response(
    request: AuthenticatedHttpRequest, application: SILApplication, context: dict[str, Any]
):
    section_1 = application.goods_section1.filter(is_active=True)
    section_2 = application.goods_section2.filter(is_active=True)
    section_5 = application.goods_section5.filter(is_active=True)
    section_58 = application.goods_section582_obsoletes.filter(is_active=True)
    section_58_other = application.goods_section582_others.filter(is_active=True)
    section_legacy = application.goods_legacy.filter(is_active=True)

    has_goods = any(
        s.exists()
        for s in (section_1, section_2, section_5, section_58, section_58_other, section_legacy)
    )

    context.update(
        {
            "process": application,
            "has_goods": has_goods,
            "goods_section_1": section_1,
            "goods_section_2": section_2,
            "goods_section_5": section_5,
            "goods_section_58": section_58,
            "goods_section_58_other": section_58_other,
            "section_legacy": section_legacy,
        }
    )

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-fa-sil-response.html",
        context=context,
    )


def _prepare_sanctions_and_adhoc_response(
    request: AuthenticatedHttpRequest,
    application: SanctionsAndAdhocApplication,
    context: dict[str, Any],
) -> HttpResponse:

    goods = annotate_commodity_unit(
        application.sanctionsandadhocapplicationgoods_set.all(), "commodity__"
    ).distinct()

    context.update({"process": application, "goods": goods})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-sanctions-response.html",
        context=context,
    )


def _prepare_derogations_response(
    request: AuthenticatedHttpRequest, application: DerogationsApplication, context: dict[str, Any]
) -> HttpResponse:
    context.update({"process": application})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-derogations-response.html",
        context=context,
    )


def _prepare_wood_quota_response(
    request: AuthenticatedHttpRequest, application: WoodQuotaApplication, context: dict[str, Any]
) -> HttpResponse:
    context.update({"process": application})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-wood-quota-response.html",
        context=context,
    )


def _prepare_opt_response(
    request: AuthenticatedHttpRequest,
    application: OutwardProcessingTradeApplication,
    context: dict[str, Any],
) -> HttpResponse:
    compensating_product_commodities = application.cp_commodities.all()
    temporary_exported_goods_commodities = application.teg_commodities.all()

    context.update(
        {
            "process": application,
            "compensating_product_commodities": compensating_product_commodities,
            "temporary_exported_goods_commodities": temporary_exported_goods_commodities,
        }
    )

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-opt-response.html",
        context=context,
    )


def _prepare_textiles_quota_response(
    request: AuthenticatedHttpRequest, application: TextilesApplication, context: dict[str, Any]
) -> HttpResponse:
    context.update({"process": application})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-textiles-quota-response.html",
        context=context,
    )


def _prepare_sps_response(
    request: AuthenticatedHttpRequest,
    application: PriorSurveillanceApplication,
    context: dict[str, Any],
) -> HttpResponse:
    context.update({"process": application})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-sps-response.html",
        context=context,
    )


def _prepare_ironsteel_response(
    request: AuthenticatedHttpRequest,
    application: PriorSurveillanceApplication,
    context: dict[str, Any],
) -> HttpResponse:
    context.update(
        {"process": application, "certificates": application.certificates.filter(is_active=True)}
    )

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-ironsteel-response.html",
        context=context,
    )


def _prepare_com_response(
    request: AuthenticatedHttpRequest,
    application: CertificateOfManufactureApplication,
    context: dict[str, Any],
) -> HttpResponse:
    context.update(
        {"process": application, "countries": application.countries.filter(is_active=True)}
    )

    return render(
        request=request,
        template_name="web/domains/case/export/manage/prepare-com-response.html",
        context=context,
    )


def _prepare_cfs_response(
    request: AuthenticatedHttpRequest,
    application: CertificateOfFreeSaleApplication,
    context: dict[str, Any],
) -> HttpResponse:
    context.update(
        {"process": application, "countries": application.countries.filter(is_active=True)}
    )

    return render(
        request=request,
        template_name="web/domains/case/export/manage/prepare-cfs-response.html",
        context=context,
    )


def _prepare_gmp_response(
    request: AuthenticatedHttpRequest,
    application: CertificateOfGoodManufacturingPracticeApplication,
    context: dict[str, Any],
) -> HttpResponse:
    context.update(
        {"process": application, "countries": application.countries.filter(is_active=True)}
    )

    return render(
        request=request,
        template_name="web/domains/case/export/manage/prepare-gmp-response.html",
        context=context,
    )
