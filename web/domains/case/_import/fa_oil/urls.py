from django.conf import settings
from django.urls import include, path

from . import views

app_name = "fa-oil"


public_urls = [
    path(
        "<int:application_pk>/",
        include(
            [
                # Firearms and Ammunition - Open Individual Licence
                path("edit/", views.edit_oil, name="edit"),
                path("submit/", views.submit_oil, name="submit-oil"),
                path(
                    "report/<int:report_pk>/firearms/",
                    include(
                        [
                            path(
                                "manual/add/",
                                views.add_report_firearm_manual,
                                name="report-firearm-manual-add",
                            ),
                            path(
                                "upload/add/",
                                views.add_report_firearm_upload,
                                name="report-firearm-upload-add",
                            ),
                            path(
                                "<int:report_firearm_pk>/",
                                include(
                                    [
                                        path(
                                            "manual/edit/",
                                            views.edit_report_firearm_manual,
                                            name="report-firearm-manual-edit",
                                        ),
                                        path(
                                            "upload/view/",
                                            views.view_upload_document,
                                            name="report-firearm-upload-view",
                                        ),
                                        path(
                                            "delete/",
                                            views.delete_report_firearm,
                                            name="report-firearm-manual-delete",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
            ],
        ),
    )
]

private_urls = [
    path("<int:application_pk>/checklist/", views.manage_checklist, name="manage-checklist"),
]

if settings.INCLUDE_PRIVATE_URLS:
    urlpatterns = public_urls + private_urls
else:
    urlpatterns = public_urls
