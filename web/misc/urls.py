from django.urls import path

from . import views

app_name = "misc"

urlpatterns = [
    path("postcode-lookup", views.postcode_lookup, name="postcode-lookup"),
    path("company-lookup", views.company_lookup, name="company-lookup"),
]
