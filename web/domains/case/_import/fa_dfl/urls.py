from django.urls import include, path

from . import views

app_name = "fa-dfl"

# Firearms and Ammunition - Deactivated Firearms Licence urls
urlpatterns = [
    path("<int:application_pk>/edit/", views.edit_dfl, name="edit"),
    path("<int:pk>/add-goods-certificate/", views.add_goods_certificate, name="add-goods"),
    path(
        "<int:application_pk>/goods-certificate/<int:document_pk>/",
        include(
            [
                path("edit/", views.edit_goods_certificate, name="edit-goods"),
                path("view/", views.view_goods_certificate, name="view-goods"),
                path("delete/", views.delete_goods_certificate, name="delete-goods"),
            ]
        ),
    ),
    path("<int:pk>/submit/", views.submit_dfl, name="submit"),
]
