from django.conf import settings
from django.urls import include, path

from . import views

app_name = "import"

firearms_urls = [
    path("fa/", include("web.domains.case._import.fa.urls")),
    path("dfl/", include("web.domains.case._import.fa_dfl.urls")),
    path("oil/", include("web.domains.case._import.fa_oil.urls")),
    path("sil/", include("web.domains.case._import.fa_sil.urls")),
]

endorsements_urls = [
    path("add/", views.add_endorsement, name="add-endorsement"),
    path("add-custom/", views.add_custom_endorsement, name="add-custom-endorsement"),
    path(
        "<int:endorsement_pk>/",
        include(
            [
                path("edit/", views.edit_endorsement, name="edit-endorsement"),
                path("delete/", views.delete_endorsement, name="delete-endorsement"),
            ]
        ),
    ),
]

# ILB Admin urls relating to viewing / managing applications that should be sent to IMI
imi_urls = [
    path("case-list", views.IMICaseListView.as_view(), name="imi-case-list"),
    path(
        "case/<int:application_pk>/",
        include(
            [
                path("summary/", views.IMICaseDetailView.as_view(), name="imi-case-detail"),
                path(
                    "confirm-information/",
                    views.imi_confirm_provided,
                    name="imi-confirm-information",
                ),
            ]
        ),
    ),
]

urlpatterns = [
    path("", views.ImportApplicationChoiceView.as_view(), name="choose"),
    # Create import application urls
    path("create/sanctions/", views.create_sanctions, name="create-sanctions"),
    path("create/derogations/", views.create_derogations, name="create-derogations"),
    path("create/firearms/dfl/", views.create_firearms_dfl, name="create-fa-dfl"),
    path("create/firearms/oil/", views.create_firearms_oil, name="create-fa-oil"),
    path("create/firearms/sil/", views.create_firearms_sil, name="create-fa-sil"),
    path("create/wood/quota/", views.create_wood_quota, name="create-wood-quota"),
    path("create/opt/", views.create_opt, name="create-opt"),
    path("create/textiles/", views.create_textiles, name="create-textiles"),
    path("create/sps/", views.create_sps, name="create-sps"),
    # Application urls
    path("derogations/", include("web.domains.case._import.derogations.urls")),
    path("sanctions/", include("web.domains.case._import.sanctions.urls")),
    path("firearms/", include(firearms_urls)),
    path("wood/", include("web.domains.case._import.wood.urls")),
    path("opt/", include("web.domains.case._import.opt.urls")),
    path("textiles/", include("web.domains.case._import.textiles.urls")),
    path("sps/", include("web.domains.case._import.sps.urls")),
    # ILB Admin Case management
    path(
        "case/<int:application_pk>/",
        include(
            [
                # These are import-specific, no reason to move them up to case-level
                path("endorsements/", include(endorsements_urls)),
                path("cover-letter/edit/", views.edit_cover_letter, name="edit-cover-letter"),
                path("licence/edit", views.edit_licence, name="edit-licence"),
            ]
        ),
    ),
    path("imi/", include(imi_urls)),
]

if not settings.SEND_LICENCE_TO_CHIEF and settings.ALLOW_BYPASS_CHIEF_NEVER_ENABLE_IN_PROD:
    urlpatterns += [
        path(
            "case/<int:application_pk>/bypass-chief/<chiefstatus:chief_status>/",
            views.bypass_chief,
            name="bypass-chief",
        )
    ]
