from django.urls import path

from . import views

app_name = "cat"
urlpatterns = [
    path("", views.CATListView.as_view(), name="list"),
    path("create/", views.create, name="create"),
    path("edit/<int:cat_pk>/", views.Edit.as_view(), name="edit"),
]
