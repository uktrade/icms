from django.urls import path

from . import views

app_name = "misc"

urlpatterns = [
    path("postcode-lookup", views.postcode_lookup, name="postcode-lookup"),
    path("company-lookup", views.company_lookup, name="company-lookup"),
    path("company-number-lookup", views.company_number_lookup, name="company-number-lookup"),
]
