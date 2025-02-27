from django.urls import path

from web.ecil.views import views_export_application as views

app_name = "export-application"
urlpatterns = [
    path(
        "another-contact/",
        views.AnotherExportApplicationContactTemplateView.as_view(),
        name="another-contact",
    ),
]
