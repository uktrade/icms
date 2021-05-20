from django.urls import include, path

from . import views

app_name = "import"

urlpatterns = [
    path("", views.ImportApplicationChoiceView.as_view(), name="choose"),
    # Create import application urls
    path("create/sanctions/", views.create_sanctions, name="create-sanctions"),
    path("create/derogations/", views.create_derogations, name="create-derogations"),
    path("create/firearms/dfl/", views.create_firearms_dfl, name="create-fa-dfl"),
    path("create/firearms/oil/", views.create_firearms_oil, name="create-fa-oil"),
    path("create/firearms/sil/", views.create_firearms_sil, name="create-fa-sil"),
    path("create/wood/quota/", views.create_wood_quota, name="create-wood-quota"),
    # Application urls
    path("derogations/", include("web.domains.case._import.derogations.urls")),
    path("sanctions/", include("web.domains.case._import.sanctions.urls")),
    path(
        "firearms/",
        include(
            [
                path("dfl/", include("web.domains.case._import.fa_dfl.urls")),
                path("oil/", include("web.domains.case._import.fa_oil.urls")),
                path("sil/", include("web.domains.case._import.fa_sil.urls")),
                # Firearms and Ammunition - Import Contact urls
                path(
                    "<int:pk>/import-contacts/",
                    views.list_import_contacts,
                    name="fa-list-import-contacts",
                ),
                path(
                    "<int:pk>/import-contacts/<entity>/create/",
                    views.create_import_contact,
                    name="fa-create-import-contact",
                ),
                path(
                    "<int:application_pk>/import-contacts/<entity>/<int:contact_pk>/edit/",
                    views.edit_import_contact,
                    name="fa-edit-import-contact",
                ),
            ]
        ),
    ),
    path("wood/", include("web.domains.case._import.wood.urls")),
    # ILB Admin Case management
    path(
        "case/<int:pk>/update-requests/",
        views.manage_update_requests,
        name="manage-update-requests",
    ),
    path(
        "case/<int:application_pk>/update-requests/<int:update_request_pk>/close/",
        views.close_update_requests,
        name="close-update-requests",
    ),
    path("case/<int:pk>/prepare-response/", views.prepare_response, name="prepare-response"),
    path("case/<int:pk>/cover-letter/", views.edit_cover_letter, name="edit-cover-letter"),
    path("case/<int:pk>/licence/", views.edit_licence, name="edit-licence"),
    path(
        "case/<int:pk>/endorsements/add/",
        views.add_endorsement,
        name="add-endorsement",
    ),
    path(
        "case/<int:pk>/endorsements/add-custom/",
        views.add_custom_endorsement,
        name="add-custom-endorsement",
    ),
    path(
        "case/<int:application_pk>/endorsements/<int:endorsement_pk>/edit/",
        views.edit_endorsement,
        name="edit-endorsement",
    ),
    path(
        "case/<int:application_pk>/endorsements/<int:endorsement_pk>/delete/",
        views.delete_endorsement,
        name="delete-endorsement",
    ),
    path(
        "case/<int:pk>/cover-letter/preview/",
        views.preview_cover_letter,
        name="preview-cover-letter",
    ),
    path("case/<int:pk>/licence/preview/", views.preview_licence, name="preview-licence"),
    path("case/<int:pk>/authorisation/", views.authorisation, name="authorisation"),
    path(
        "case/<int:pk>/start-authorisation/", views.start_authorisation, name="start-authorisation"
    ),
    path(
        "case/<int:pk>/cancel-authorisation/",
        views.cancel_authorisation,
        name="cancel-authorisation",
    ),
]
