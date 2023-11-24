import django.contrib.auth.views as auth_views
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import Form
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import CreateView, FormView
from django_ratelimit.decorators import ratelimit

from web.auth.utils import migrate_user
from web.types import AuthenticatedHttpRequest

from .forms import AccountRecoveryForm, UserCreationForm


class RegisterView(CreateView):
    template_name = "registration/register.html"
    form_class = UserCreationForm

    def get_success_url(self):
        return reverse(settings.LOGIN_URL)


class LoginView(auth_views.LoginView):
    extra_context = {"ilb_contact_email": settings.ILB_CONTACT_EMAIL}

    @method_decorator(ratelimit(key="ip", rate="20/m", block=True))
    @method_decorator(ratelimit(key="post:username", rate="10/m", block=True))
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Rate limit users by IP and username.

        Stops a user trying to brute force a single username as well as trying different usernames from the same IP.
        Consider this in the future to create a soft blocking mechanism:
        https://django-ratelimit.readthedocs.io/en/stable/security.html#denial-of-service
        """

        return super().post(request, *args, **kwargs)


class LegacyAccountRecoveryView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    # FormView config
    form_class = AccountRecoveryForm
    success_url = reverse_lazy("login-start")
    template_name = "registration/v1_account_recovery.html"

    # Mark all POST parameters as sensitive
    @method_decorator(sensitive_post_parameters())
    def dispatch(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)

    def test_func(self) -> bool:
        """Only allow account recovery for user accounts that haven't come from V1."""

        return not self.request.user.icms_v1_user

    @method_decorator(ratelimit(key="ip", rate="20/m", block=True))
    @method_decorator(ratelimit(key="post:legacy_email", rate="10/m", block=True))
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Rate limit users by IP and username.

        Stops a user trying to brute force a single legacy_email as well as trying different legacy_emails from the same IP.
        Consider this in the future to create a soft blocking mechanism:
        https://django-ratelimit.readthedocs.io/en/stable/security.html#denial-of-service
        """
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        legacy_user = form.cleaned_data["legacy_user"]

        # Link the current user with the v1 account
        migrate_user(self.request.user, legacy_user)

        # Clear the users session
        auth.logout(self.request)

        # Redirect to the login page.
        return super().form_valid(form)
