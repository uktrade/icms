from operator import attrgetter

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http.response import HttpResponse
from django.shortcuts import render

from web.permissions import Perms
from web.sites import is_exporter_site, is_importer_site
from web.types import AuthenticatedHttpRequest

from .actions.applicant_actions import ShowWelcomeMessageAction
from .app_data import get_applicant_qs, get_ilb_admin_qs, get_sanctions_case_officer_qs
from .base import WorkbasketRow, WorkbasketSection
from .row import get_workbasket_row_func


@login_required
def show_workbasket(request: AuthenticatedHttpRequest) -> HttpResponse:
    is_ilb_admin = request.user.has_perm(Perms.sys.ilb_admin)

    # Users with sanctions_case_officer are also ilb_admin's so check this first.
    # The goal is to restrict the records shown to sanctions case officers.
    if request.user.has_perm(Perms.sys.sanctions_case_officer):
        qs = get_sanctions_case_officer_qs(request.user)
    elif is_ilb_admin:
        qs = get_ilb_admin_qs(request.user)
    else:
        qs = get_applicant_qs(request.user)

    qs_list = list(qs)

    # Order all records before pagination
    qs_list.sort(key=attrgetter("order_datetime"), reverse=True)

    paginator = Paginator(qs_list, settings.WORKBASKET_PER_PAGE)
    page_number = request.GET.get("page", default=1)

    page_obj = paginator.get_page(page_number)

    # Only call get_workbasket_row on the row's being rendered
    rows = []

    for r in page_obj:
        get_workbasket_row = get_workbasket_row_func(r.process_type)
        row = get_workbasket_row(r, request.user, is_ilb_admin)

        rows.append(row)

    # Add custom welcome action for new users of ICMS (excluding ILB Admins)
    if is_importer_site(request.site) or is_exporter_site(request.site):
        welcome_action = ShowWelcomeMessageAction(request.user)

        if welcome_action.show_link() and not is_ilb_admin:
            actions = welcome_action.get_workbasket_actions()
            welcome_section = WorkbasketSection(
                information=actions[0].section_label,  # type: ignore[arg-type]
                actions=actions,
            )

            welcome_row = WorkbasketRow(
                id=-1,  # id is only used for end-to-end tests
                reference="",
                subject=f"Account successfully created\n{request.user.full_name}",
                company="",
                company_agent="",
                status="WELCOME_TO_ICMS",
                timestamp=None,
                sections=[welcome_section],
            )

            rows = [welcome_row] + rows

    context = {"page_title": "Workbasket", "rows": rows, "page_obj": page_obj}

    return render(request, "web/domains/workbasket/workbasket.html", context)
