from django.urls import path

from web.ecil.views import views_new_user as views

app_name = "new_user"
urlpatterns = [
    path(
        "exporter-login-start/", views.ExporterLoginStartView.as_view(), name="exporter_login_start"
    ),
]
