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
    re_path(
        "case/(?P<application_pk>[0-9]+)/(?P<entity>importer|exporter)/view/$",
        views.case_view,
        name="case-view",
    ),
    path(
        "case/<int:application_pk>/firs/list/",
        views.list_firs,
        name="list-firs",
    ),
    path(
        "case/<int:application_pk>/firs/<int:fir_pk>/respond/",
        views.respond_fir,
        name="respond-fir",
    ),
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
    # management for further information requests
    path("case/<int:application_pk>/firs/manage/", views.manage_firs, name="manage-firs"),
    path("case/<int:application_pk>/firs/add/", views.add_fir, name="add-fir"),
    path("case/<int:application_pk>/firs/<int:fir_pk>/edit/", views.edit_fir, name="edit-fir"),
    path(
        "case/<int:application_pk>/firs/<int:fir_pk>/archive/",
        views.archive_fir,
        name="archive-fir",
    ),
    path(
        "case/<int:application_pk>/firs/<int:fir_pk>/withdraw/",
        views.withdraw_fir,
        name="withdraw-fir",
    ),
    path("case/<int:application_pk>/firs/<int:fir_pk>/close/", views.close_fir, name="close-fir"),
    path(
        "case/<int:application_pk>/firs/<int:fir_pk/files/<int:file_pk/archive/",
        views.archive_fir_file,
        name="archive-fir-file",
    ),
]
