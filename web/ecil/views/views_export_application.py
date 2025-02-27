from typing import Any
from urllib import parse

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.urls import Resolver404, ResolverMatch, resolve, reverse
from django.views.generic import TemplateView

from web.ecil.gds.component_serializers import back_link, notification_banner
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest


class AnotherExportApplicationContactTemplateView(
    LoginRequiredMixin, PermissionRequiredMixin, TemplateView
):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # TemplateView
    http_method_names = ["get"]
    template_name = "ecil/export_application/another_contact.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["notification_banner_kwargs"] = notification_banner.NotificationBannerKwargs(
            text=(
                "If you want someone else to be the main contact for the application,"
                " they need to be linked to the exporter"
            ),
        ).model_dump(exclude_defaults=True)

        referrer_view = self.request.session.get("referrer_view")
        referrer_view_kwargs = self.request.session.get("referrer_view_kwargs")

        if referrer_view and referrer_view_kwargs:
            url = reverse(referrer_view, kwargs=referrer_view_kwargs)
            context["back_link_kwargs"] = back_link.BackLinkKwargs(
                text="Back", href=url
            ).model_dump(exclude_defaults=True)

        return context

    # TODO: Revisit in ECIL-638 (HTTP_REFERER view mixin / middleware)
    def get(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        # Store the referrer url for back link
        referrer = self.request.META.get("HTTP_REFERER", "")
        referrer_path: str = parse.urlparse(referrer).path

        try:
            resolver_match: ResolverMatch = resolve(referrer_path)
            self.request.session["referrer_view"] = resolver_match.view_name
            if resolver_match.kwargs:
                self.request.session["referrer_view_kwargs"] = resolver_match.kwargs

        except Resolver404:
            pass

        return super().get(request, *args, **kwargs)
