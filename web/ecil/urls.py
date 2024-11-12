from django.urls import path

from . import views

app_name = "ecil"
urlpatterns = [
    path("gds-example/", views.GDSTestPage.as_view(), name="gds_example"),
]
