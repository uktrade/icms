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
                path(
                    "contact/",
                    views.CFSApplicationContactUpdateView.as_view(),
                    name="application-contact",
                ),
                path("schedule/", views.CFSScheduleCreateView.as_view(), name="schedule-create"),
                path(
                    "schedule/<int:schedule_pk>/",
                    include(
                        [
                            path(
                                "exporter-status/",
                                views.CFSScheduleExporterStatusUpdateView.as_view(),
                                name="schedule-exporter-status",
                            ),
                            path(
                                "manufacturer-address/",
                                views.CFSScheduleManufacturerAddressUpdateView.as_view(),
                                name="schedule-manufacturer-address",
                            ),
                            path(
                                "brand-name-holder/",
                                views.CFSScheduleBrandNameHolderUpdateView.as_view(),
                                name="schedule-brand-name-holder",
                            ),
                            path(
                                "country-of-manufacture/",
                                views.CFSScheduleCountryOfManufactureUpdateView.as_view(),
                                name="schedule-country-of-manufacture",
                            ),
                            path(
                                "legislation/",
                                views.CFSScheduleAddLegislationUpdateView.as_view(),
                                name="schedule-legislation",
                            ),
                        ],
                    ),
                ),
            ]
        ),
    ),
]
