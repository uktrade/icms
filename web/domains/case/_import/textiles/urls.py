from django.urls import include, path

from . import views

app_name = "textiles"

urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                path("edit/", views.edit_textiles, name="edit"),
                # TODO: leaving these in since we'll need them
                # path("submit/", views.submit_textiles, name="submit"),
                # path(
                #     "document/",
                #     include(
                #         [
                #             path("add/<str:file_type>", views.add_document, name="add-document"),
                #             path(
                #                 "<int:document_pk>/",
                #                 include(
                #                     [
                #                         path("view/", views.view_document, name="view-document"),
                #                         path(
                #                             "delete/", views.delete_document, name="delete-document"
                #                         ),
                #                     ]
                #                 ),
                #             ),
                #         ]
                #     ),
                # ),
                # path("checklist/", views.manage_checklist, name="manage-checklist"),
            ],
        ),
    )
]
