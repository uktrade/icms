from django.urls import path

from . import views

app_name = "fa-dfl"

# Firearms and Ammunition - Deactivated Firearms Licence urls
urlpatterns = [
    path("<int:pk>/edit/", views.edit_dlf, name="edit"),
]
