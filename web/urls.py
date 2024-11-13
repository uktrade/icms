from django.conf import settings
from django.urls import include, path, register_converter

from web import converters
from web.domains.checker.views import V1ToV2RedirectCheckCertificateView
from web.registration.views import LegacyAccountRecoveryView
from web.views import (
    LoginRequiredSelect2AutoResponseView,
    RedirectBaseDomainView,
    V1ToV2ServiceRenameView,
    cookie_consent_view,
    health_check,
    home,
    login_start_view,
    logout_view,
)

register_converter(converters.NegativeIntConverter, "negint")
register_converter(converters.CaseTypeConverter, "casetype")
register_converter(converters.ExportApplicationTypeConverter, "exportapplicationtype")
register_converter(converters.SILSectionTypeConverter, "silsectiontype")
register_converter(converters.EntityTypeConverter, "entitytype")
register_converter(converters.OrgTypeConverter, "orgtype")
register_converter(converters.ChiefStatusConverter, "chiefstatus")


# The following urls are served by all deployed instances of ICMS
public_urls = [
    #
    # ICMS auth urls to direct users to correct auth mechanism.
    path("", RedirectBaseDomainView.as_view()),
    path("login-start/", login_start_view, name="login-start"),
    path("logout/", logout_view, name="logout-user"),
    path("ecil/", include("web.ecil.urls")),
    #
    # staff-sso-client login urls
    path("auth/", include("authbroker_client.urls")),
    #
    # gov-uk-one-login urls
    path("one-login/", include("web.one_login.urls")),
    #
    # ICMS V1 Account recovery view
    path("account-recovery/", LegacyAccountRecoveryView.as_view(), name="account-recovery"),
    #
    # Application urls
    path("home/", home, name="home"),
    path("access/", include("web.domains.case.access.urls", namespace="access")),
    path("case/", include("web.domains.case.urls")),
    path("cat/", include("web.domains.cat.urls")),
    path("check/", include("web.domains.checker.urls")),
    path("contacts/", include("web.domains.contacts.urls")),
    path("export/", include("web.domains.case.export.urls", namespace="export")),
    path("exporter/", include("web.domains.exporter.urls")),
    path("import/", include("web.domains.case._import.urls")),
    path("importer/", include("web.domains.importer.urls")),
    path("mailshot/", include("web.domains.mailshot.urls")),
    path("misc/", include("web.misc.urls")),
    path("user/", include("web.domains.user.urls")),
    path("workbasket/", include("web.domains.workbasket.urls")),
    #
    # Health check url
    path("health-check/", health_check, name="health-check"),
    path("pingdom/ping.xml", health_check, name="dbt-platform-health-check"),
    #
    # Django select2 urls
    path("select2/", include("django_select2.urls")),
    path(
        "django-select2/fields/authenticated-auto.json",
        LoginRequiredSelect2AutoResponseView.as_view(),
        name="login-required-select2-view",
    ),
    # Cookie consent URLs
    path("cookie-consent/", cookie_consent_view, name="cookie-consent"),
    path("support/", include("web.support.urls")),
    # V1->V2 certificate checker
    path(
        "icms/fox/icms/IMP_CERT_CERTIFICATE_CHECKER/check/",
        V1ToV2RedirectCheckCertificateView.as_view(),
    ),
    path(
        "icmsfox5live/fox/icms/IMP_CERT_CERTIFICATE_CHECKER/check/",
        V1ToV2RedirectCheckCertificateView.as_view(),
    ),
    # Users who have bookmarked the old V1 url
    path(
        "icms/fox/icms/",
        V1ToV2ServiceRenameView.as_view(),
    ),
    path(
        "icmsfox5live/fox/icms/",
        V1ToV2ServiceRenameView.as_view(),
    ),
    # Users who have bookmarked the old V1 url (extra importer login url)
    path(
        "icms/fox/live/IMP_LOGIN/login",
        V1ToV2ServiceRenameView.as_view(),
    ),
    path(
        "icmsfox5live/fox/live/IMP_LOGIN/login",
        V1ToV2ServiceRenameView.as_view(),
    ),
]

# The following urls should only be served on the private application
private_urls = [
    path("constabulary/", include("web.domains.constabulary.urls")),
    path("signature/", include("web.domains.signature.urls")),
    path("template/", include("web.domains.template.urls")),
    path("commodity/", include("web.domains.commodity.urls")),
    path("chief/", include("web.domains.chief.urls", namespace="chief")),
    path("sanction-emails/", include("web.domains.sanction_email.urls")),
    path("section5/", include("web.domains.section5.urls")),
    path("firearms/", include("web.domains.firearms.urls")),
    path("product-legislation/", include("web.domains.legislation.urls")),
    path("country/", include("web.domains.country.urls")),
    path("reports/", include("web.reports.urls")),
]

if settings.INCLUDE_PRIVATE_URLS:
    urlpatterns = public_urls + private_urls
else:
    urlpatterns = public_urls


if settings.DEBUG:
    urlpatterns.extend([path("test-harness/", include("web.harness.urls"))])

#
# Add django model auth login urls for local development
if not settings.STAFF_SSO_ENABLED or not settings.GOV_UK_ONE_LOGIN_ENABLED:
    urlpatterns.extend([path("accounts/", include("web.registration.urls"))])
