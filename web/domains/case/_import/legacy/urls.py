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
]
