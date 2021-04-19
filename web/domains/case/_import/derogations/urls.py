from django.urls import path

from . import views

app_name = "derogations"

urlpatterns = [
    path("<int:pk>/edit/", views.edit_derogations, name="edit-derogations"),
    path(
        "<int:pk>/add-supporting-document/",
        views.add_supporting_document,
        name="add-supporting-document",
    ),
    path(
        "<int:application_pk>/view-supporting-document/<int:document_pk>/",
        views.view_supporting_document,
        name="view-supporting-document",
    ),
    path(
        "<int:application_pk>/delete-supporting-document/<int:document_pk>/",
        views.delete_supporting_document,
        name="delete-supporting-document",
    ),
    path("<int:pk>/submit/", views.submit_derogations, name="submit-derogations"),
]
