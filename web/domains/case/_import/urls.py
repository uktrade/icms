from django.urls import path

from web.domains.case._import.views import (
    ImportApplicationChoiceView,
    create_oil,
    edit_oil,
)

urlpatterns = [
    path("", ImportApplicationChoiceView.as_view(), name="new-import-application"),
    # firearms and ammunition
    path("firearms/oil/create/", create_oil, name="create-oil"),
    path("firearms/oil/<int:pk>/edit/", edit_oil, name="edit-oil"),
]
