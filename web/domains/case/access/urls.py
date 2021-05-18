from django.urls import include, path, re_path

from . import views

app_name = "access"
urlpatterns = [
    # access request list for ilb admin
    path("importer/", views.ListImporterAccessRequest.as_view(), name="importer-list"),
    path("exporter/", views.ListExporterAccessRequest.as_view(), name="exporter-list"),
    # access request made by user
    path("importer/request/", views.importer_access_request, name="importer-request"),
    path("exporter/request/", views.exporter_access_request, name="exporter-request"),
    path("requested/", views.AccessRequestCreatedView.as_view(), name="requested"),
    # access request management
    re_path(
        "^case/(?P<pk>[0-9]+)/(?P<entity>importer|exporter)/management/$",
        views.management,
        name="case-management",
    ),
    re_path(
        "^case/(?P<pk>[0-9]+)/(?P<entity>importer|exporter)/close-access-request/$",
        views.management_response,
        name="case-management-response",
    ),
    # approval request
    path("", include("web.domains.case.access.approval.urls")),
]
