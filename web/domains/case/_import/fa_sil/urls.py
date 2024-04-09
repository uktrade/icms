from django.urls import include, path

from . import views

app_name = "fa-sil"

urlpatterns = [
    path(
        "<int:application_pk>/",
        include(
            [
                path("edit/", views.edit, name="edit"),
                path("submit/", views.submit, name="submit"),
                path("checklist/", views.manage_checklist, name="manage-checklist"),
                path("set-cover-letter/", views.set_cover_letter, name="set-cover-letter"),
                # Goods
                path("sections/choose/", views.choose_goods_section, name="choose-goods-section"),
                path(
                    "<silsectiontype:sil_section_type>/",
                    include(
                        [
                            path("add/", views.add_section, name="add-section"),
                            path(
                                "<int:section_pk>/",
                                include(
                                    [
                                        path("edit/", views.edit_section, name="edit-section"),
                                        path(
                                            "delete/", views.delete_section, name="delete-section"
                                        ),
                                        path(
                                            "response-prep-edit-goods/",
                                            views.response_preparation_edit_goods,
                                            name="response-prep-edit-goods",
                                        ),
                                    ]
                                ),
                            ),
                            path(
                                "<int:section_pk>/report/<int:report_pk>/firearms/",
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
                ),
                # User section 5 authorities
                path(
                    "user-section5/",
                    include(
                        [
                            path("add/", views.add_section5_document, name="add-section5-document"),
                            path(
                                "<int:section5_pk>/",
                                include(
                                    [
                                        path(
                                            "archive/",
                                            views.archive_section5_document,
                                            name="archive-section5-document",
                                        ),
                                        path(
                                            "view/",
                                            views.view_section5_document,
                                            name="view-section5-document",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                # Verified user section 5 authorities
                path(
                    "verified-section5/",
                    include(
                        [
                            path(
                                "<int:section5_pk>/",
                                include(
                                    [
                                        path(
                                            "add/",
                                            views.add_verified_section5,
                                            name="add-verified-section5",
                                        ),
                                        path(
                                            "delete/",
                                            views.delete_verified_section5,
                                            name="delete-verified-section5",
                                        ),
                                        path(
                                            "view/",
                                            views.view_verified_section5,
                                            name="view-verified-section5",
                                        ),
                                    ]
                                ),
                            ),
                            path(
                                "document/<int:document_pk>/view/",
                                views.view_verified_section5_document,
                                name="view-verified-section5-document",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
