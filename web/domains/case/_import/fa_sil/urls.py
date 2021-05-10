from django.urls import path

from . import views

app_name = "fa-sil"
urlpatterns = [
    path("<int:pk>/edit/", views.edit, name="edit"),
]
