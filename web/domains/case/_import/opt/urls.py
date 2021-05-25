from django.urls import include, path

from . import views

app_name = "opt"

urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                path("edit/", views.edit_opt, name="edit"),
                path("submit/", views.submit_opt, name="submit"),
            ]
        ),
    )
]
