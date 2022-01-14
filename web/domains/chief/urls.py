from django.urls import path

from . import views

app_name = "chief"
urlpatterns = [
    path(
        "license-data-callback", views.LicenseDataCallback.as_view(), name="license-data-callback"
    ),
]
