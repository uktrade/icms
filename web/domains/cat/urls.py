from django.urls import path

from . import views

app_name = "cat"
urlpatterns = [
    path("", views.CATListView.as_view(), name="list"),
]
