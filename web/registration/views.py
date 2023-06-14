import django.contrib.auth.views as auth_views
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from ratelimit.decorators import ratelimit

from .forms import UserCreationForm


class RegisterView(CreateView):
    template_name = "registration/register.html"
    form_class = UserCreationForm

    def get_success_url(self):
        return reverse("accounts:login")


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
