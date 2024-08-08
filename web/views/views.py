import logging
from typing import Any
from urllib import parse
from urllib.parse import urljoin

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import resolve, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.defaults import permission_denied
from django.views.generic import RedirectView, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django_filters import FilterSet
from django_select2.views import AutoResponseView

from web.domains.case.shared import ImpExpStatus
from web.flow.errors import ProcessError, ProcessStatusError, TaskError
from web.models import Task
from web.one_login.utils import get_one_login_logout_url
from web.sites import (
    get_exporter_site_domain,
    get_importer_site_domain,
    is_caseworker_site,
    is_exporter_site,
    is_importer_site,
)
from web.utils.sentry import capture_exception

from .actions import PostAction
from .forms import CookieConsentForm
from .mixins import DataDisplayConfigMixin, PageTitleMixin

logger = logging.getLogger(__name__)


class RedirectBaseDomainView(RedirectView):
    """Redirects base url visits to either workbasket or login."""

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            self.url = reverse("workbasket")
        else:
            self.url = reverse("login-start")

        return super().get_redirect_url(*args, **kwargs)


def login_start_view(request: HttpRequest) -> HttpResponse:
    """Custom login view to handle redirecting to correct authentication backend."""

    if settings.STAFF_SSO_ENABLED:
        staff_sso_login_url = reverse("authbroker_client:login")
    else:
        # Default login for environments where staff-sso is disabled.
        staff_sso_login_url = reverse("accounts:login")

    if settings.GOV_UK_ONE_LOGIN_ENABLED:
        one_login_login_url = reverse("one_login:login")
    else:
        # Default login for environments where one-login is disabled.
        one_login_login_url = reverse("accounts:login")

    staff_sso_login_url, one_login_login_url = _add_next_qp_to_login_urls(
        request, staff_sso_login_url, one_login_login_url
    )

    if is_importer_site(request.site):
        extra = {
            "service_description": "Use this service to apply for an import licence",
            "auth_login_url": one_login_login_url,
            "show_one_login_msg": True,
        }
    elif is_exporter_site(request.site):
        extra = {
            "service_description": "Use this service to apply for an export certificate",
            "auth_login_url": one_login_login_url,
            "show_one_login_msg": True,
        }
    elif is_caseworker_site(request.site):
        extra = {
            "service_description": "",
            "auth_login_url": staff_sso_login_url,
            "show_one_login_msg": False,
        }
    else:
        raise PermissionDenied

    context = {
        "service_title": request.site.name,
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
    } | extra

    return render(request, "login_start.html", context)


def _add_next_qp_to_login_urls(request, staff_sso_login_url, one_login_login_url):
    """Forward the ?next= query param to the auth login urls."""

    url: parse.ParseResult = parse.urlparse(request.get_full_path())
    query_params: dict[str, Any] = parse.parse_qs(url.query)

    next_qp = query_params.get(auth.REDIRECT_FIELD_NAME)
    if next_qp:
        next_encoded = parse.urlencode({auth.REDIRECT_FIELD_NAME: next_qp[0]})
        staff_sso_login_url = f"{staff_sso_login_url}?{next_encoded}"
        one_login_login_url = f"{one_login_login_url}?{next_encoded}"

    return staff_sso_login_url, one_login_login_url


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    """Custom logout view to handle redirecting to correct redirect url."""
    # 1. Fetch cached backend for user
    backend = request.session.get(auth.BACKEND_SESSION_KEY, "")

    # 2. Using user backend, set correct auth logout view.
    login_start = reverse("login-start")
    match backend:
        case "web.auth.backends.ICMSStaffSSOBackend":
            url = parse.urljoin(settings.AUTHBROKER_URL, "logout/")

        case "web.auth.backends.ICMSGovUKOneLoginBackend":
            if is_exporter_site(request.site):
                site = get_exporter_site_domain()
            elif is_importer_site(request.site):
                site = get_importer_site_domain()
            else:
                raise ValueError(f"Unable to determine site: {request.site}")

            url = get_one_login_logout_url(request, urljoin(site, reverse("login-start")))

        case "web.auth.backends.ModelAndObjectPermissionBackend":
            url = login_start

        case _:
            logger.error(f"Unknown backend: {backend}, defaulting to login_start")
            url = login_start

    # 3. Clear session and user
    auth.logout(request)

    # 4. Redirect to correct logout url.
    return redirect(url)


@login_required
def home(request):
    return render(request, "web/home.html")


def cookie_consent_view(request: HttpRequest) -> HttpResponse:
    """View for the cookie consent page. More info can be found in the README under Google Analytics."""
    if request.method == "GET":
        initial_dict = {}

        if current_cookies_policy := request.COOKIES.get("accepted_ga_cookies"):
            initial_dict["accept_cookies"] = current_cookies_policy == "true"

        return render(
            request,
            "web/cookie-consent.html",
            context={"form": CookieConsentForm(initial=initial_dict)},
        )
    else:
        form = CookieConsentForm(request.POST)
        if form.is_valid():
            # cookie consent stuff lasts for 1 year
            cookie_max_age = 365 * 24 * 60 * 60

            referrer_url = request.GET.get("referrer_url", "/")
            if not url_has_allowed_host_and_scheme(
                referrer_url, settings.ALLOWED_HOSTS, require_https=request.is_secure()
            ):
                # if the referrer URL is not allowed, redirect to the home page
                referrer_url = "/"
            response = redirect(referrer_url)

            # regardless of their choice, we set a cookie to say they've made a choice
            response.set_cookie("cookie_preferences_set", "true", max_age=cookie_max_age)

            response.set_cookie(
                "accepted_ga_cookies",
                "true" if form.cleaned_data["accept_cookies"] else "false",
                max_age=cookie_max_age,
            )

            return response
        else:
            return render(request, "web/cookie-consent.html", context={"form": form})


def handler403_capture_process_error_view(
    request: HttpRequest, exception: Exception
) -> HttpResponseForbidden:
    """Custom 403 handler to send ProcessError exceptions to sentry.

    https://docs.sentry.io/platforms/python/integrations/django/http_errors/
    """

    # Process errors are a subclass of PermissionDenied
    # Two potential scenarios:
    #     1. We have a bug with our expected status or expected task checking.
    #     2. A user is accessing a view they can't access via the UI, e.g. loading the edit view
    #        after an application has been submitted.
    # We care about the first scenario as it will require a code change, e.g. change the expected
    # status a view is checking for.
    # We do not care about the second, and the user will see a custom 403 error page.
    # We don't strictly need request.user.is_anonymous as the login required decorator / mixin
    # should have returned them to the login page before now.
    # I am just being paranoid about returning different templates for valid requests.
    if isinstance(exception, ProcessError) and not request.user.is_anonymous:
        view_name = resolve(request.path).view_name

        # ProcessStatusError is a subclass of ProcessError
        if isinstance(exception, ProcessStatusError):
            if can_ignore_process_status_error(exception, view_name):
                # The handler403 function must return a HttpResponseForbidden instance
                # Therefore the only option we have is to override the template.
                return permission_denied(
                    request, exception, template_name="403_view_no_longer_available.html"
                )

            # Capture ProcessErrors that we haven't handled above.
            capture_exception()

        # TaskError is a subclass of ProcessError
        if isinstance(exception, TaskError):
            if can_ignore_task_error(exception, view_name):
                # The handler403 function must return a HttpResponseForbidden instance
                # Therefore the only option we have is to override the template.
                return permission_denied(
                    request, exception, template_name="403_view_no_longer_available.html"
                )

            # Capture TaskError that we haven't handled above.
            capture_exception()

    return permission_denied(request, exception)


def can_ignore_process_status_error(exception: ProcessStatusError, view_name: str) -> bool:
    """Returns True if the status / view_name can be safely ignored.

    This doesn't capture every view possible, just the views that change the status.
    e.g. a user presses submit and then presses back.

    :param exception: ProcessStatusError instance raised
    :param view_name: name of the view being requested
    """

    # Importer / Exporter user has pressed back after pressing submit
    if exception.app_status == ImpExpStatus.SUBMITTED and view_name in [
        # Import application submit views
        "import:fa-oil:submit-oil",
        "import:fa-dfl:submit",
        "import:fa-sil:submit",
        "import:sanctions:submit-sanctions",
        "import:wood:submit-quota",
        # Export application submit views
        "export:com-submit",
        "export:cfs-submit",
        "export:gmp-submit",
    ]:
        return True

    return False


def can_ignore_task_error(exception: TaskError, view_name: str) -> bool:
    """Returns True if the status, task & view_name can be safely ignored.

    This doesn't capture every view possible, just the views that change the an expected task.
    e.g. A case officer presses authorise and then presses back.

    :param exception: TaskError instance raised
    :param view_name: name of the view being requested
    """

    # Caseworker has pressed back after pressing Authorise
    if (
        exception.app_status in [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        and exception.expected_task == Task.TaskType.PROCESS
        and view_name == "case:start-authorisation"
    ):
        return True

    return False


class LoginRequiredSelect2AutoResponseView(LoginRequiredMixin, AutoResponseView):
    """Login required Django Select 2 AutoResponseView."""

    raise_exception = True


class ModelFilterView(
    PermissionRequiredMixin, LoginRequiredMixin, DataDisplayConfigMixin, ListView
):
    paginate_by = 50
    paginate = True
    default_filters: dict | None = None
    filterset_class: type[FilterSet]

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        actions = getattr(self.Display, "actions", [])
        for a in actions:
            if isinstance(a, PostAction) and a.action == action:
                response = a.handle(request, self, *args, **kwargs)
                if response:
                    return response

        # Render the same page
        return super().get(request, *args, **kwargs)

    def get_page(self):
        return self.request.GET.get("page")

    def _paginate(self, queryset):
        paginator = Paginator(queryset, self.paginate_by)
        page = self.get_page()

        try:
            return paginator.page(page)
        except PageNotAnInteger:
            return paginator.page(1)
        except EmptyPage:
            return paginator.page(paginator.num_pages)

    def get_filterset(self, **kwargs: Any) -> FilterSet:
        queryset = self.get_queryset()

        if self.is_initial_page_load():
            filterset_data = self.default_filters
            queryset = self.get_initial_data(queryset)
        else:
            filterset_data = self.request.GET

        return self.filterset_class(
            filterset_data, queryset=queryset, request=self.request, **kwargs
        )

    def is_initial_page_load(self):
        """Work out if this view has been loaded for the first time.

        Evaluates to True if there are no query params or the params supplied do not match
        the filterset fields.
        This is to allow the views to work correctly with extra query params that have nothing
        to do with filtering the queryset.
        """

        if not self.request.GET:
            return True

        form_filters = set(self.filterset_class.declared_filters.keys())
        request_query_params = set(self.request.GET.keys())

        return form_filters.isdisjoint(request_query_params)

    def get_initial_data(self, queryset: QuerySet) -> QuerySet:
        """Do not show results until a search has been performed by default"""
        return queryset.none()

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        filterset = self.get_filterset()
        context["filter"] = filterset
        if self.paginate:
            context["page"] = self._paginate(filterset.qs)
        else:
            context["results"] = filterset.qs

        context["initial_page_load"] = self.is_initial_page_load()

        return context


class ModelCreateView(
    PermissionRequiredMixin, LoginRequiredMixin, PageTitleMixin, SuccessMessageMixin, CreateView
):
    template_name = "model/edit.html"

    def get_success_message(self, cleaned_data):
        return f"{self.object} created successfully."


class ModelUpdateView(
    PermissionRequiredMixin, LoginRequiredMixin, PageTitleMixin, SuccessMessageMixin, UpdateView
):
    template_name = "model/edit.html"

    def get_success_message(self, cleaned_data):
        return f"{self.object} updated successfully"

    def get_page_title(self):
        return f"Editing {self.object}"


class ModelDetailView(PermissionRequiredMixin, LoginRequiredMixin, PageTitleMixin, DetailView):
    template_name = "model/view.html"

    def _readonly(self, form):
        for key in form.fields.keys():
            form.fields[key].disabled = True
        return form

    def get_form(self, instance=None):
        """Create new instance of form and make readonly"""
        form = self.form_class(instance=instance)
        return self._readonly(form)

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form(instance=self.get_object())
        return context

    def get_page_title(self):
        return f"Viewing {self.object}"


class AccessibilityStatementView(TemplateView):
    http_method_names = ["get"]
    template_name = "web/accessibility_statement.html"


class V1ToV2ServiceRenameView(TemplateView):
    """View detailing service name change for users who have bookmarked the V1 URL."""

    http_method_names = ["get"]
    template_name = "web/v1_user_bookmark_info.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context | {
            "import_a_licence_url": get_importer_site_domain(),
            "export_a_certificate_url": get_exporter_site_domain(),
        }
