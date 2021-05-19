from django.urls import include, path

from . import views

app_name = "fa-sil"
urlpatterns = [
    path("<int:pk>/edit/", views.edit, name="edit"),
    path("<int:pk>/submit/", views.submit, name="submit"),
    # Goods
    path("<int:pk>/sections/choose/", views.choose_goods_section, name="choose-goods-section"),
    path(
        "<int:application_pk>/<silsectiontype:sil_section_type>/",
        include(
            [
                path("add/", views.add_section, name="add-section"),
                path("<int:section_pk>/edit/", views.edit_section, name="edit-section"),
                path("<int:section_pk>/delete/", views.delete_section, name="delete-section"),
            ]
        ),
    ),
]
