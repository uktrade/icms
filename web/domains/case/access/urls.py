from django.urls import path, re_path

from . import views


app_name = "access"
urlpatterns = [
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
        "^case/(?P<pk>[0-9]+)/(?P<entity>importer|exporter)/access-approval/$",
        views.management_access_approval,
        name="case-management-access-approval",
    ),
    re_path(
        "^case/(?P<pk>[0-9]+)/(?P<entity>importer|exporter)/close-access-request/$",
        views.management_response,
        name="case-management-response",
    ),
]
