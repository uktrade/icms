from django.urls import path

from . import views

urlpatterns = [
    path("quota/<int:pk>/edit/", views.edit_wood_quota, name="edit-wood-quota"),
]
