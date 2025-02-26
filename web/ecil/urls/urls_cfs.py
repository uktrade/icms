from django.urls import include, path

from web.ecil.views import views_cfs as views

app_name = "export-cfs"
urlpatterns = [
    path(
        "application/<int:application_pk>/",
        include(
            [
                path(
                    "reference/",
                    views.CFSApplicationReferenceUpdateView.as_view(),
                    name="application-reference",
                ),
            ]
        ),
    ),
]
