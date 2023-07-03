from django.urls import include, path

from . import views

app_name = "constabulary"

urlpatterns = [
    path("", views.ConstabularyListView.as_view(), name="list"),
    path("new/", views.ConstabularyCreateView.as_view(), name="new"),
    path(
        "<int:pk>/",
        include(
            [
                path("", views.ConstabularyDetailView.as_view(), name="detail"),
                path("edit/", views.ConstabularyEditView.as_view(), name="edit"),
                path(
                    "contact/add/",
                    views.AddConstabularyContactView.as_view(),
                    name="add-contact",
                ),
                path(
                    "contact/delete/<int:contact_pk>",
                    views.DeleteConstabularyContactView.as_view(),
                    name="delete-contact",
                ),
            ]
        ),
    ),
]
