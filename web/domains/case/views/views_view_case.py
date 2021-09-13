from typing import TYPE_CHECKING, NamedTuple

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from web.domains.case._import.opt.forms import FurtherQuestionsBaseOPTForm
from web.domains.case._import.opt.utils import get_fq_form, get_fq_page_name
from web.domains.case._import.textiles.models import TextilesApplication
from web.domains.case.export.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CFSSchedule,
)
from web.models import (
    AccessRequest,
    CertificateOfManufactureApplication,
    CommodityGroup,
    DerogationsApplication,
    DFLApplication,
    ExporterAccessRequest,
    GMPFile,
    ImporterAccessRequest,
    IronSteelApplication,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    OutwardProcessingTradeFile,
    PriorSurveillanceApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    WoodQuotaApplication,
)
from web.types import AuthenticatedHttpRequest
from web.utils.commodity import annotate_commodity_unit

from ..types import ImpOrExpOrAccess
from ..utils import check_application_permission, get_case_page_title
from .utils import get_class_imp_or_exp_or_access

if TYPE_CHECKING:
    from django.db.models import QuerySet


class OPTFurtherQuestionsSharedSection(NamedTuple):
    form: FurtherQuestionsBaseOPTForm
    section_title: str
    supporting_documents: "QuerySet[OutwardProcessingTradeFile]"


@login_required
def view_case(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp_or_access(case_type)
    application: ImpOrExpOrAccess = get_object_or_404(model_class, pk=application_pk)

    check_application_permission(application, request.user, case_type)

    # Access Requests
    if application.process_type == ImporterAccessRequest.PROCESS_TYPE:
        return _view_accessrequest(request, application.importeraccessrequest)  # type: ignore[union-attr]

    elif application.process_type == ExporterAccessRequest.PROCESS_TYPE:
        return _view_accessrequest(request, application.exporteraccessrequest)  # type: ignore[union-attr]

    # Import applications
    if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
        return _view_fa_oil(request, application.openindividuallicenceapplication)  # type: ignore[union-attr]

    elif application.process_type == SILApplication.PROCESS_TYPE:
        return _view_fa_sil(request, application.silapplication)  # type: ignore[union-attr]

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        return _view_sanctions_and_adhoc(request, application.sanctionsandadhocapplication)  # type: ignore[union-attr]

    elif application.process_type == WoodQuotaApplication.PROCESS_TYPE:
        return _view_wood_quota(request, application.woodquotaapplication)  # type: ignore[union-attr]

    elif application.process_type == DerogationsApplication.PROCESS_TYPE:
        return _view_derogations(request, application.derogationsapplication)  # type: ignore[union-attr]

    elif application.process_type == DFLApplication.PROCESS_TYPE:
        return _view_dfl(request, application.dflapplication)  # type: ignore[union-attr]

    elif application.process_type == OutwardProcessingTradeApplication.PROCESS_TYPE:
        return _view_opt(request, application.outwardprocessingtradeapplication)  # type: ignore[union-attr]

    elif application.process_type == TextilesApplication.PROCESS_TYPE:
        return _view_textiles_quota(request, application.textilesapplication)  # type: ignore[union-attr]

    elif application.process_type == PriorSurveillanceApplication.PROCESS_TYPE:
        return _view_sps(request, application.priorsurveillanceapplication)  # type: ignore[union-attr]

    elif application.process_type == IronSteelApplication.PROCESS_TYPE:
        return _view_ironsteel(request, application.ironsteelapplication)  # type: ignore[union-attr]

    # Export applications
    elif application.process_type == CertificateOfManufactureApplication.PROCESS_TYPE:
        return _view_com(request, application.certificateofmanufactureapplication)  # type: ignore[union-attr]

    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        return _view_cfs(request, application.certificateoffreesaleapplication)

    elif application.process_type == CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE:
        return _view_gmp(request, application.certificateofgoodmanufacturingpracticeapplication)

    else:
        raise NotImplementedError(f"Unknown process_type {application.process_type}")


def _view_fa_oil(
    request: AuthenticatedHttpRequest, application: OpenIndividualLicenceApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "verified_certificates": application.verified_certificates.filter(is_active=True),
        "certificates": application.user_imported_certificates.active(),
        "contacts": application.importcontact_set.all(),
    }

    return render(request, "web/domains/case/import/fa-oil/view.html", context)


def _view_fa_sil(
    request: AuthenticatedHttpRequest, application: OpenIndividualLicenceApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "verified_certificates": application.verified_certificates.filter(is_active=True),
        "certificates": application.user_imported_certificates.active(),
        "verified_section5": application.importer.section5_authorities.currently_active(),
        "user_section5": application.user_section5.filter(is_active=True),
        "contacts": application.importcontact_set.all(),
    }

    return render(request, "web/domains/case/import/fa-sil/view.html", context)


def _view_sanctions_and_adhoc(
    request: AuthenticatedHttpRequest, application: SanctionsAndAdhocApplication
) -> HttpResponse:

    goods = annotate_commodity_unit(
        application.sanctionsandadhocapplicationgoods_set.all(), "commodity__"
    ).distinct()

    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "goods": goods,
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/sanctions/view.html", context)


def _view_wood_quota(
    request: AuthenticatedHttpRequest, application: WoodQuotaApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "contract_documents": application.contract_documents.filter(is_active=True),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/wood/view.html", context)


def _view_derogations(
    request: AuthenticatedHttpRequest, application: DerogationsApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/derogations/view.html", context)


def _view_dfl(request: AuthenticatedHttpRequest, application: DFLApplication) -> HttpResponse:
    goods_list = application.goods_certificates.filter(is_active=True).select_related(
        "issuing_country"
    )
    contact_list = application.importcontact_set.all()

    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "goods_list": goods_list,
        "contacts": contact_list,
    }

    return render(request, "web/domains/case/import/fa-dfl/view.html", context)


def _view_opt(
    request: AuthenticatedHttpRequest, application: OutwardProcessingTradeApplication
) -> HttpResponse:
    group = CommodityGroup.objects.get(
        commodity_type__type_code="TEXTILES", group_code=application.cp_category
    )
    category_group_description = group.group_description

    # Reuse the model verbose_name for the labels
    opt_fields = OutwardProcessingTradeApplication._meta.get_fields()
    labels = {f.name: getattr(f, "verbose_name", "") for f in opt_fields}

    # Reuse the forms to render the different further questions sections
    # key=section name, value=template context
    fq_sections: dict[str, OPTFurtherQuestionsSharedSection] = {}

    for file_type in OutwardProcessingTradeFile.Type:  # type: ignore[attr-defined]
        if file_type != OutwardProcessingTradeFile.Type.SUPPORTING_DOCUMENT:
            form_class = get_fq_form(file_type)
            section_title = get_fq_page_name(file_type)

            form = form_class(instance=application, has_files=False)
            supporting_documents = application.documents.filter(is_active=True, file_type=file_type)

            fq_sections[file_type] = OPTFurtherQuestionsSharedSection(
                form=form, section_title=section_title, supporting_documents=supporting_documents
            )

    # Supporting docs for the main form:
    supporting_documents = application.documents.filter(
        is_active=True, file_type=OutwardProcessingTradeFile.Type.SUPPORTING_DOCUMENT
    )

    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "category_group_description": category_group_description,
        "labels": labels,
        "fq_sections": fq_sections,
        "supporting_documents": supporting_documents,
    }

    return render(request, "web/domains/case/import/opt/view.html", context)


def _view_textiles_quota(
    request: AuthenticatedHttpRequest, application: TextilesApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/textiles/view.html", context)


def _view_sps(
    request: AuthenticatedHttpRequest, application: PriorSurveillanceApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/sps/view.html", context)


def _view_ironsteel(
    request: AuthenticatedHttpRequest, application: IronSteelApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
        "certificates": application.certificates.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/ironsteel/view.html", context)


def _view_accessrequest(
    request: AuthenticatedHttpRequest, application: AccessRequest
) -> HttpResponse:
    context = {
        "process": application,
        "page_title": get_case_page_title("access", application, "View"),
    }

    return render(request, "web/domains/case/access/case-view.html", context)


def _view_com(
    request: AuthenticatedHttpRequest, application: CertificateOfManufactureApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/export/partials/process.html",
        "process": application,
        "page_title": get_case_page_title("export", application, "View"),
    }

    return render(request, "web/domains/case/export/com/view.html", context)


def _view_cfs(request: AuthenticatedHttpRequest, application: CertificateOfFreeSaleApplication):

    # Reuse the model verbose_name for the labels
    cfs_fields = CFSSchedule._meta.get_fields()
    labels = {f.name: getattr(f, "verbose_name", "") for f in cfs_fields}
    app_countries = "\n".join(application.countries.all().values_list("name", flat=True))

    context = {
        "process_template": "web/domains/case/export/partials/process.html",
        "process": application,
        "labels": labels,
        "application_countries": app_countries,
        "schedules": application.schedules.filter(is_active=True).order_by("created_at"),
        "page_title": get_case_page_title("export", application, "View"),
    }

    return render(request, "web/domains/case/export/cfs-view.html", context)


def _view_gmp(
    request: AuthenticatedHttpRequest,
    application: CertificateOfGoodManufacturingPracticeApplication,
) -> HttpResponse:
    show_iso_table = application.gmp_certificate_issued == application.CertificateTypes.ISO_22716
    show_brc_table = application.gmp_certificate_issued == application.CertificateTypes.BRC_GSOCP

    context = {
        "process_template": "web/domains/case/export/partials/process.html",
        "process": application,
        "page_title": get_case_page_title("export", application, "View"),
        "country": application.countries.first(),
        "show_iso_table": show_iso_table,
        "show_brc_table": show_brc_table,
        "GMPFileTypes": GMPFile.Type,
    }

    return render(request, "web/domains/case/export/gmp-view.html", context)
