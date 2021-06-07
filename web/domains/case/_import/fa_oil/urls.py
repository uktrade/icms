from django.urls import path

from . import views

app_name = "fa-oil"


urlpatterns = [
    # Firearms and Ammunition - Open Individual Licence
    path("<int:application_pk>/edit/", views.edit_oil, name="edit"),
    path("<int:pk>/submit/", views.submit_oil, name="submit-oil"),
    # Firearms and Ammunition - Management by ILB Admin
    path("case/<int:pk>/checklist/", views.manage_checklist, name="manage-checklist"),
    # Firearms and Ammunition - Verified Certificates
    path(
        "<int:application_pk>/authority/<int:authority_pk>/toggle/",
        views.toggle_verified_firearms,
        name="toggle-verified-firearms",
    ),
    path(
        "<int:application_pk>/authority/<int:authority_pk>/view/",
        views.view_verified_firearms,
        name="view-verified-firearms",
    ),
    path(
        "<int:application_pk>/authority/<int:authority_pk>/files/<int:file_pk>/view/",
        views.view_verified_certificate_file,
        name="view-verified-certificate-file",
    ),
]
