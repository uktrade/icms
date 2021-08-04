from django.urls import include, path

from . import views

app_name = "ironsteel"

supporting_document_urls = [
    path("add/", views.add_document, name="add-document"),
    path(
        "<int:document_pk>/",
        include(
            [
                path("view/", views.view_document, name="view-document"),
                path("delete/", views.delete_document, name="delete-document"),
            ]
        ),
    ),
]

certificate_urls = [
    path("add/", views.add_certificate, name="add-certificate"),
    path(
        "<int:document_pk>/",
        include(
            [
                path("view/", views.view_certificate, name="view-certificate"),
                path("delete/", views.delete_certificate, name="delete-certificate"),
                path("edit/", views.edit_certificate, name="edit-certificate"),
            ]
        ),
    ),
]

urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                path("edit/", views.edit_ironsteel, name="edit"),
                path("submit/", views.submit_ironsteel, name="submit"),
                path("document/", include(supporting_document_urls)),
                path("certificate/", include(certificate_urls)),
                # Case management
                path("checklist/", views.manage_checklist, name="manage-checklist"),
            ],
        ),
    )
]
