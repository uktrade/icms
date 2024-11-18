from django.urls import path

from . import views

app_name = "ecil"
urlpatterns = [
    path("gds-example/", views.GDSTestPageView.as_view(), name="gds_example"),
    path("gds-form-example/", views.GDSFormView.as_view(), name="gds_form_example"),
]
