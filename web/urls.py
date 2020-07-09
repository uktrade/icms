from django.urls import include, path, register_converter

from . import converters

from .views import home

register_converter(converters.NegativeIntConverter, "negint")

urlpatterns = [
    path("", include("web.auth.urls")),
    path("home/", home, name="home"),
    path("workbasket/", include("web.domains.workbasket.urls")),
    path("user/", include("web.domains.user.urls")),
    path("template/", include("web.domains.template.urls")),
    path("teams/", include("web.domains.team.urls")),
    path("constabulary/", include("web.domains.constabulary.urls")),
    path("commodity/", include("web.domains.commodity.urls")),
    path("country/", include("web.domains.country.urls")),
    path("product-legislation/", include("web.domains.legislation.urls")),
    path("firearms/", include("web.domains.firearms.urls")),
    path("importer/", include("web.domains.importer.urls")),
    path("exporter/", include("web.domains.exporter.urls")),
    path("access/", include("web.domains.case.access.urls", namespace="access")),
    path("import/", include("web.domains.application._import.urls")),
    path("mailshot/", include("web.domains.mailshot.urls")),
]
