from django.urls import path

from . import views

app_name = "chief"
urlpatterns = [
    path("pending-licences/", views.PendingLicences.as_view(), name="pending-licences"),
    path("failed-licences/", views.FailedLicences.as_view(), name="failed-licences"),
    path(
        "request-data/<int:litehmrcchiefrequest_id>",
        views.ChiefRequestDataView.as_view(),
        name="request-data",
    ),
    path(
        "resend-licence/<int:application_pk>",
        views.ResendLicenceToChiefView.as_view(),
        name="resend-licence",
    ),
    path(
        "check-progress/<int:application_pk>",
        views.CheckChiefProgressView.as_view(),
        name="check-progress",
    ),
    # The LITE_API_URL path configured in icms-hmrc.
    path(
        "license-data-callback", views.LicenseDataCallback.as_view(), name="license-data-callback"
    ),
]
