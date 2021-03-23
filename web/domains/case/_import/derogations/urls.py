from django.urls import path

from . import views

app_name = "derogations"

urlpatterns = [
    path("<int:pk>/edit/", views.edit_derogations, name="edit-derogations"),
    path("<int:pk>/submit/", views.submit_derogations, name="submit-derogations"),
]
