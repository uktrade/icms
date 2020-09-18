from django.urls import path

from . import views

app_name = "export"

urlpatterns = [
    path("create", views.ExportApplicationCreateView.as_view(), name="create"),
    path("com/<int:pk>/edit/", views.edit_com, name="com-edit"),
    path("com/<int:pk>/submit/", views.submit_com, name="com-submit"),
    path("case/<int:pk>/take_ownership/", views.take_ownership, name="case-take-ownership"),
    path(
        "case/<int:pk>/release_ownership/", views.release_ownership, name="case-release-ownership",
    ),
    path("case/<int:pk>/management/", views.Management.as_view(), name="case-management"),
    # TODO: add certificate of free sale URLs
]
