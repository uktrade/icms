from django.urls import path

from . import views

app_name = "legacy"

urlpatterns = [
    # Outward Processing Trade (OPT) legacy urls
    path(
        "opt/<int:application_pk>/document/<int:document_pk>/view/",
        views.opt_view_document,
        name="opt-view-document",
    ),
    path(
        "opt/<int:application_pk>/checklist/",
        views.opt_manage_checklist,
        name="opt-manage-checklist",
    ),
    # Textiles (TEX) legacy urls
    path(
        "tex/<int:application_pk>/document/<int:document_pk>/view/",
        views.tex_view_document,
        name="tex-view-document",
    ),
    path(
        "tex/<int:application_pk>/checklist/",
        views.tex_manage_checklist,
        name="tex-manage-checklist",
    ),
    # Prior Surveillance (SPS) legacy urls
    path(
        "sps/<int:application_pk>/contract-document/view/",
        views.sps_view_contract_document,
        name="sps-view-contract-document",
    ),
    path(
        "sps/<int:application_pk>/support-document/<int:document_pk>/view/",
        views.sps_view_supporting_document,
        name="sps-view-supporting-document",
    ),
]
