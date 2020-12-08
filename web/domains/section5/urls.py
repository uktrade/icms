from django.urls import path

from web.domains.section5.views import (
    ListSection5,
    archive_section5,
    create_section5,
    edit_section5,
    unarchive_section5,
)

app_name = "section5"
urlpatterns = [
    path("", ListSection5.as_view(), name="list"),
    path("create/", create_section5, name="create"),
    path("edit/<int:pk>/", edit_section5, name="edit"),
    path("archive/<int:pk>/", archive_section5, name="archive"),
    path("unarchive/<int:pk>/", unarchive_section5, name="unarchive"),
]
