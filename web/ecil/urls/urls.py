from django.urls import include, path

app_name = "ecil"
urlpatterns = [
    path("example/", include("web.ecil.urls.urls_example")),
    path("new-user/", include("web.ecil.urls.urls_new_user")),
    path("access-request/", include("web.ecil.urls.urls_access_requests")),
]
