from django.urls import path

from . import views

app_name = "wood"

urlpatterns = [
    path("quota/<int:pk>/edit/", views.edit_wood_quota, name="edit-quota"),
    path(
        "quota/<int:pk>/add-supporting-document/",
        views.add_supporting_document,
        name="add-supporting-document",
    ),
    path(
        "quota/<int:application_pk>/view-supporting-document/<int:document_pk>/",
        views.view_supporting_document,
        name="view-supporting-document",
    ),
    path(
        "quota/<int:application_pk>/delete-supporting-document/<int:document_pk>/",
        views.delete_supporting_document,
        name="delete-supporting-document",
    ),
]
