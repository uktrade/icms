from django.urls import include, path

from . import views

app_name = "fa-oil"


urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                # Firearms and Ammunition - Open Individual Licence
                path("edit/", views.edit_oil, name="edit"),
                path("submit/", views.submit_oil, name="submit-oil"),
                # Firearms and Ammunition - Management by ILB Admin
                path("checklist/", views.manage_checklist, name="manage-checklist"),
            ],
        ),
    )
]
