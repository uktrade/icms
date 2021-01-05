from django.urls import path

from .views import (
    EndorsementCreateView,
    TemplateEditView,
    TemplateListView,
    archive_endorsement_usage_link,
    create_cfs_declaration_translation,
    edit_cfs_declaration_translation,
    edit_endorsement_usage,
    list_endorsement_usages,
    view_template_fwd,
)

urlpatterns = [
    path("", TemplateListView.as_view(), name="template-list"),
    path("<int:pk>/", view_template_fwd, name="template-view"),
    path("<int:pk>/edit/", TemplateEditView.as_view(), name="template-edit"),
    path(
        "cfs-declaration-translation/new/",
        create_cfs_declaration_translation,
        name="template-cfs-declaration-translation-new",
    ),
    path(
        "cfs-declaration-translation/<int:pk>/edit/",
        edit_cfs_declaration_translation,
        name="template-cfs-declaration-translation-edit",
    ),
    path("endorsement/new/", EndorsementCreateView.as_view(), name="template-endorsement-new"),
    path("endorsement/usages/", list_endorsement_usages, name="template-endorsement-usages"),
    path(
        "endorsement/usages/<int:pk>/edit/",
        edit_endorsement_usage,
        name="template-endorsement-usage-edit",
    ),
    path(
        "endorsement/usages/<int:usage_pk>link/<int:link_pk>/archive/",
        archive_endorsement_usage_link,
        name="template-endorsement-usage-link-archive",
    ),
]
