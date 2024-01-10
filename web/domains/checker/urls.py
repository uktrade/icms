from django.urls import path

from . import views

app_name = "checker"
urlpatterns = [
    path("", views.check_certificate, name="certificate-checker"),
]
