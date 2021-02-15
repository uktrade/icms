from django.urls import re_path

from . import views

urlpatterns = [
    re_path(
        "applicant-details/(?P<pk>[0-9]+)/",
        views.sanctions_show_applicant_details,
        name="sanctions-show-applicant-details",
    ),
    re_path(
        "sanctions-and-adhoc-licence-application-details/(?P<pk>[0-9]+)/",
        views.sanctions_and_adhoc_licence_application_details,
        name="sanctions-and-adhoc-licence-application-details",
    ),
    re_path(
        "validation-summary/(?P<pk>[0-9]+)/",
        views.sanctions_validation_summary,
        name="sanctions-validation-summary",
    ),
    re_path(
        "application-submit/(?P<pk>[0-9]+)/",
        views.sanctions_application_submit,
        name="sanctions-submit",
    ),
]
