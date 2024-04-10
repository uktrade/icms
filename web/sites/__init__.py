import functools
from typing import Any

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

from web.permissions import Perms
from web.types import AuthenticatedHttpRequest, TypedTextChoices


class SiteName(TypedTextChoices):
    CASEWORKER = (
        "Manage import licences and export certificates",
        "Manage import licences and export certificates",
    )
    EXPORTER = ("Apply for an export certificate", "Apply for an export certificate")
    IMPORTER = ("Apply for an import licence", "Apply for an import licence")


def require_importer(check_permission=True):
    def decorator(f):
        """Decorator to require that a view only accepts requests from the importer site."""

        @functools.wraps(f)
        def _wrapped_view(
            request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any
        ) -> HttpResponse:
            if not is_importer_site(request.site):
                raise PermissionDenied("Importer feature requires importer site.")

            if check_permission and not request.user.has_perm(Perms.sys.importer_access):
                raise PermissionDenied("Importer feature requires importer access.")

            return f(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def require_exporter(check_permission=True):
    def decorator(f):
        """Decorator to require that a view only accepts requests from the exporter site."""

        @functools.wraps(f)
        def _wrapped_view(
            request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any
        ) -> HttpResponse:
            if not is_exporter_site(request.site):
                raise PermissionDenied("Exporter feature requires exporter site.")

            if check_permission and not request.user.has_perm(Perms.sys.exporter_access):
                raise PermissionDenied("Exporter feature requires exporter access.")

            return f(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def is_exporter_site(site: Site) -> bool:
    return site.name == SiteName.EXPORTER


def is_importer_site(site: Site) -> bool:
    return site.name == SiteName.IMPORTER


def is_caseworker_site(site: Site) -> bool:
    return site.name == SiteName.CASEWORKER


def get_caseworker_site_domain() -> str:
    return _get_site_domain(SiteName.CASEWORKER)


def get_exporter_site_domain() -> str:
    return _get_site_domain(SiteName.EXPORTER)


def get_importer_site_domain() -> str:
    return _get_site_domain(SiteName.IMPORTER)


def _get_site_domain(name: SiteName) -> str:
    """Return a site domain with the scheme included."""
    scheme = "https" if settings.APP_ENV not in ["local", "test"] else "http"
    domain = Site.objects.get(name=name).domain

    return f"{scheme}://{domain}"
