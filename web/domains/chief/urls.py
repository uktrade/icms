from django.urls import path

from . import views

app_name = "chief"
urlpatterns = [
    path("", views.PendingBatches.as_view(), name="pending-batches"),
    path("failed-batches/", views.FailedBatches.as_view(), name="failed-batches"),
    path("pending-licences/", views.PendingLicences.as_view(), name="pending-licences"),
    path("failed-licences/", views.FailedLicences.as_view(), name="failed-licences"),
    # The LITE_API_URL path configured in icms-hmrc.
    path(
        "license-data-callback", views.LicenseDataCallback.as_view(), name="license-data-callback"
    ),
]
