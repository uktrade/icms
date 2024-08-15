from django.urls import include, path

from . import views

app_name = "fa-dfl"

# Firearms and Ammunition - Deactivated Firearms Licence urls
urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                path("edit/", views.edit_dfl, name="edit"),
                path(
                    "goods-certificate/",
                    include(
                        [
                            path("add/", views.add_goods_certificate, name="add-goods"),
                            path(
                                "list/",
                                views.DFLGoodsCertificateDetailView.as_view(),
                                name="list-goods",
                            ),
                            path(
                                "<int:document_pk>/",
                                include(
                                    [
                                        path(
                                            "edit/", views.edit_goods_certificate, name="edit-goods"
                                        ),
                                        path(
                                            "edit-description/",
                                            views.edit_goods_certificate_description,
                                            name="edit-goods-description",
                                        ),
                                        path(
                                            "reset-description/",
                                            views.reset_goods_certificate_description,
                                            name="reset-goods-description",
                                        ),
                                        path(
                                            "view/", views.view_goods_certificate, name="view-goods"
                                        ),
                                        path(
                                            "delete/",
                                            views.delete_goods_certificate,
                                            name="delete-goods",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                path("submit/", views.submit_dfl, name="submit"),
                path("checklist/", views.manage_checklist, name="manage-checklist"),
                path(
                    "report/<int:report_pk>/firearms/",
                    include(
                        [
                            path(
                                "goods/<int:goods_pk>/",
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
                                            "no-firearm/add/",
                                            views.add_report_firearm_no_firearm,
                                            name="report-firearm-no-firearm-add",
                                        ),
                                    ]
                                ),
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
            ]
        ),
    )
]
