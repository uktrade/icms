import datetime as dt
from typing import NamedTuple

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from web.domains.case._import.opt.forms import FurtherQuestionsBaseOPTForm
from web.domains.case._import.opt.utils import get_fq_form, get_fq_page_name
from web.domains.case.types import ImpOrExp
from web.domains.case.utils import get_case_page_title
from web.models import (
    AccessRequest,
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    CFSSchedule,
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
    TextilesApplication,
    User,
    WoodQuotaApplication,
)
from web.permissions import AppChecker
from web.types import AuthenticatedHttpRequest
from web.utils.commodity import annotate_commodity_unit

from .utils import get_class_imp_or_exp


class OPTFurtherQuestionsSharedSection(NamedTuple):
    form: FurtherQuestionsBaseOPTForm
    section_title: str
    supporting_documents: "QuerySet[OutwardProcessingTradeFile]"


def check_can_view_application(user: User, application: ImpOrExp) -> None:
    checker = AppChecker(user, application)

    if not checker.can_view():
        raise PermissionDenied


@login_required
def view_case(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    # Load the record and check the correct permissions
    match case_type:
        case "access":
            application = get_object_or_404(AccessRequest, pk=application_pk)
            if request.user != application.submitted_by:
                raise PermissionDenied

        case "import" | "export":
            model_class = get_class_imp_or_exp(case_type)
            application = get_object_or_404(model_class, pk=application_pk)
            check_can_view_application(request.user, application)
        case _:
            raise ValueError(f"Unknown case_type {case_type}")

    app = application.get_specific_model()
    match app:
        #
        # Access Requests
        #
        case ImporterAccessRequest():
            return _view_accessrequest(request, app)
        case ExporterAccessRequest():
            return _view_accessrequest(request, app)
        #
        # Import applications
        #
        case OpenIndividualLicenceApplication():
            return _view_fa_oil(request, app)

        case SILApplication():
            return _view_fa_sil(request, app)

        case SanctionsAndAdhocApplication():
            return _view_sanctions_and_adhoc(request, app)

        case WoodQuotaApplication():
            return _view_wood_quota(request, app)

        case DerogationsApplication():
            return _view_derogations(request, app)

        case DFLApplication():
            return _view_dfl(request, app)

        case OutwardProcessingTradeApplication():
            return _view_opt(request, app)

        case TextilesApplication():
            return _view_textiles_quota(request, app)

        case PriorSurveillanceApplication():
            return _view_sps(request, app)

        case IronSteelApplication():
            return _view_ironsteel(request, app)
        #
        # Export applications
        #
        case CertificateOfManufactureApplication():
            return _view_com(request, app)

        case CertificateOfFreeSaleApplication():
            return _view_cfs(request, app)

        case CertificateOfGoodManufacturingPracticeApplication():
            return _view_gmp(request, app)

        case _:
            raise NotImplementedError(f"Unknown process_type {application.process_type}")


def _view_fa_oil(
    request: AuthenticatedHttpRequest, application: OpenIndividualLicenceApplication
) -> HttpResponse:
    context = {
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "verified_certificates": application.verified_certificates.filter(is_active=True),
        "certificates": application.user_imported_certificates.active(),
        "contacts": application.importcontact_set.all(),
    }

    return render(request, "web/domains/case/import/fa-oil/view.html", context)


def _view_fa_sil(request: AuthenticatedHttpRequest, application: SILApplication) -> HttpResponse:
    context = {
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "verified_certificates": application.verified_certificates.filter(is_active=True),
        "certificates": application.user_imported_certificates.active(),
        "user_section5": application.user_section5.filter(is_active=True),
        "verified_section5": application.verified_section5.exists(),
        "available_verified_section5": None,
        "selected_section5": application.verified_section5.all(),
        "contacts": application.importcontact_set.all(),
    }

    return render(request, "web/domains/case/import/fa-sil/view.html", context)


def _view_sanctions_and_adhoc(
    request: AuthenticatedHttpRequest, application: SanctionsAndAdhocApplication
) -> HttpResponse:
    goods = annotate_commodity_unit(application.sanctions_goods.all(), "commodity__").distinct()

    context = {
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

    for file_type in OutwardProcessingTradeFile.Type:
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
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/textiles/view.html", context)


def _view_sps(
    request: AuthenticatedHttpRequest, application: PriorSurveillanceApplication
) -> HttpResponse:
    context = {
        "process": application,
        "page_title": get_case_page_title("import", application, "View"),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/sps/view.html", context)


def _view_ironsteel(
    request: AuthenticatedHttpRequest, application: IronSteelApplication
) -> HttpResponse:
    context = {
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
        "process": application,
        "page_title": get_case_page_title("export", application, "View"),
    }

    return render(request, "web/domains/case/export/com/view.html", context)


def _view_cfs(
    request: AuthenticatedHttpRequest, application: CertificateOfFreeSaleApplication
) -> HttpResponse:
    # Reuse the model verbose_name for the labels
    cfs_fields = CFSSchedule._meta.get_fields()
    labels = {f.name: getattr(f, "verbose_name", "") for f in cfs_fields}
    app_countries = "\n".join(application.countries.all().values_list("name", flat=True))

    context = {
        "process": application,
        "labels": labels,
        "application_countries": app_countries,
        "schedules": application.schedules.all().order_by("created_at"),
        "page_title": get_case_page_title("export", application, "View"),
        "show_eu_fields": application.submit_datetime < dt.datetime(2021, 1, 1, tzinfo=dt.UTC),
    }

    return render(request, "web/domains/case/export/cfs-view.html", context)


def _view_gmp(
    request: AuthenticatedHttpRequest,
    application: CertificateOfGoodManufacturingPracticeApplication,
) -> HttpResponse:
    show_iso_table = application.gmp_certificate_issued == application.CertificateTypes.ISO_22716
    show_brc_table = application.gmp_certificate_issued == application.CertificateTypes.BRC_GSOCP

    context = {
        "process": application,
        "page_title": get_case_page_title("export", application, "View"),
        "country": application.countries.first(),
        "show_iso_table": show_iso_table,
        "show_brc_table": show_brc_table,
        "GMPFileTypes": GMPFile.Type,
    }

    return render(request, "web/domains/case/export/gmp-view.html", context)
