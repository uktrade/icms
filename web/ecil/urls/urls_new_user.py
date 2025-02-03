from django.urls import path

from web.ecil.views import views_new_user as views

app_name = "new_user"
urlpatterns = [
    path(
        "exporter-login-start/", views.ExporterLoginStartView.as_view(), name="exporter_login_start"
    ),
    path("what-is-your-name/", views.NewUserUpdateNameView.as_view(), name="update_name"),
    path(
        "what-are-you-applying-for/",
        views.NewUserExporterTriageFormView.as_view(),
        name="exporter_triage",
    ),
    path(
        "something-else/",
        views.NewUserExporterTriageSomethingElseView.as_view(),
        name="something_else",
    ),
]
