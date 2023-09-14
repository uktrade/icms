import functools

from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied

from web.permissions import Perms
from web.types import AuthenticatedHttpRequest

CASEWORKER_SITE_NAME = "Caseworker"
EXPORTER_SITE_NAME = "Export A Certificate"
IMPORTER_SITE_NAME = "Import A Licence"


def require_importer(check_permission=True):
    def decorator(f):
        """Decorator to require that a view only accepts requests from the importer site."""

        @functools.wraps(f)
        def _wrapped_view(request: AuthenticatedHttpRequest, *args, **kwargs):
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
        def _wrapped_view(request: AuthenticatedHttpRequest, *args, **kwargs):
            if not is_exporter_site(request.site):
                raise PermissionDenied("Exporter feature requires exporter site.")

            if check_permission and not request.user.has_perm(Perms.sys.exporter_access):
                raise PermissionDenied("Exporter feature requires exporter access.")

            return f(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def is_exporter_site(site: Site) -> bool:
    return site.name == EXPORTER_SITE_NAME


def is_importer_site(site: Site) -> bool:
    return site.name == IMPORTER_SITE_NAME


def get_caseworker_site_domain() -> str:
    return _get_site_domain(CASEWORKER_SITE_NAME)


def get_exporter_site_domain() -> str:
    return _get_site_domain(EXPORTER_SITE_NAME)


def get_importer_site_domain() -> str:
    return _get_site_domain(IMPORTER_SITE_NAME)


def _get_site_domain(name: str) -> str:
    return Site.objects.get(name=name).domain
