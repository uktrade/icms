from django.conf import settings
from django.urls import include, path, re_path

from . import views

app_name = "access"

public_urls = [
    # access request made by user
    path("importer/request/", views.importer_access_request, name="importer-request"),
    path("exporter/request/", views.exporter_access_request, name="exporter-request"),
    path("requested/", views.AccessRequestCreatedView.as_view(), name="requested"),
    # approval request
    path("", include("web.domains.case.access.approval.urls")),
]

private_urls = [
    # access request list for ilb admin
    # admin
    path("importer/", views.ListImporterAccessRequest.as_view(), name="importer-list"),
    # admin
    path("exporter/", views.ListExporterAccessRequest.as_view(), name="exporter-list"),
    # access request management
    re_path(
        "^case/(?P<access_request_pk>[0-9]+)/(?P<entity>importer|exporter)/link-access-request/$",
        views.link_access_request,
        name="link-request",
    ),
    path(
        "case/<int:access_request_pk>/<orgtype:entity>/link-access-request-agent/",
        views.LinkOrgAgentAccessRequestUpdateView.as_view(),
        name="link-access-request-agent",
    ),
    re_path(
        "^case/(?P<access_request_pk>[0-9]+)/(?P<entity>importer|exporter)/close-access-request/$",
        views.close_access_request,
        name="close-request",
    ),
    path(
        "access_request/<int:access_request_pk>/history/",
        views.AccessRequestHistoryView.as_view(),
        name="request-history",
    ),
]

if settings.INCLUDE_PRIVATE_URLS:
    urlpatterns = public_urls + private_urls
else:
    urlpatterns = public_urls
