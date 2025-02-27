from django.urls import include, path

app_name = "ecil"
urlpatterns = [
    path("access-request/", include("web.ecil.urls.urls_access_requests")),
    path("cfs/", include("web.ecil.urls.urls_cfs")),
    path("example/", include("web.ecil.urls.urls_example")),
    path("export-application/", include("web.ecil.urls.urls_export_application")),
    path("new-user/", include("web.ecil.urls.urls_new_user")),
]
