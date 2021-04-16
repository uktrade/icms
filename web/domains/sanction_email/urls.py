from django.urls import path

from . import views

app_name = "sanction-emails"
urlpatterns = [
    path("", views.SanctionEmailsListView.as_view(), name="list"),
    path("create/", views.create_sanction_email, name="create"),
    path(
        "<int:pk>/edit/",
        views.edit_sanction_email,
        name="edit",
    ),
]
