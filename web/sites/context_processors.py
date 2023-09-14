from django.http import HttpRequest

from . import is_exporter_site, is_importer_site


def sites(request: HttpRequest) -> dict[str, bool]:
    return {
        "is_importer_site": is_importer_site(request.site),
        "is_exporter_site": is_exporter_site(request.site),
    }
