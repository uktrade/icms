from django.urls import include, path

from . import views

app_name = "ironsteel"

urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                path("edit/", views.edit_ironsteel, name="edit"),
                # path("submit/", views.submit_ironsteel, name="submit"),
            ],
        ),
    )
]
