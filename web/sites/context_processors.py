from django.http import HttpRequest

from . import SiteName, is_exporter_site, is_importer_site


def sites(request: HttpRequest) -> dict[str, bool | str]:
    return {
        "is_importer_site": is_importer_site(request.site),
        "is_exporter_site": is_exporter_site(request.site),
        "exporter_site_name": SiteName.EXPORTER.label,
        "importer_site_name": SiteName.IMPORTER.label,
        "caseworker_site_name": SiteName.CASEWORKER.label,
    }
