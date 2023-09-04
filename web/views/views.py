import logging
from typing import Any
from urllib import parse

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from web.one_login.utils import OneLoginConfig

from .actions import PostAction
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

    context = {
        "staff_sso_login_url": staff_sso_login_url,
        "one_login_login_url": one_login_login_url,
    }

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

    # 2. Clear session and user
    auth.logout(request)

    # 3. Using user backend, redirect to correct auth logout view.
    login_start = reverse("login-start")
    match backend:
        case "web.auth.backends.ICMSStaffSSOBackend":
            url = parse.urljoin(settings.AUTHBROKER_URL, "logout/")

        case "web.auth.backends.ICMSGovUKOneLoginBackend":
            url = OneLoginConfig().end_session_url

        case "web.auth.backends.ModelAndObjectPermissionBackend":
            url = login_start

        case _:
            logger.error(f"Unknown backend: {backend}, defaulting to login_start")
            url = login_start

    return redirect(url)


@login_required
def home(request):
    return render(request, "web/home.html")


class ModelFilterView(
    PermissionRequiredMixin, LoginRequiredMixin, DataDisplayConfigMixin, ListView
):
    paginate_by = 50
    paginate = True

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

    def get_filterset(self, **kwargs):
        return self.filterset_class(
            self.request.GET or None, queryset=self.get_queryset(), **kwargs
        )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        filterset = self.get_filterset()
        context["filter"] = filterset
        if self.paginate:
            context["page"] = self._paginate(filterset.qs)
        else:
            context["results"] = filterset.qs
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
