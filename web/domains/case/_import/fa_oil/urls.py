from django.urls import path

from . import views

app_name = "fa-oil"


urlpatterns = [
    # Firearms and Ammunition - Open Individual Licence
    path("<int:application_pk>/edit/", views.edit_oil, name="edit"),
    path("<int:pk>/submit/", views.submit_oil, name="submit-oil"),
    # Firearms and Ammunition - Management by ILB Admin
    path("case/<int:application_pk>/checklist/", views.manage_checklist, name="manage-checklist"),
]
