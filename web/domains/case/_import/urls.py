from django.urls import include, path

from . import views

app_name = "import"

urlpatterns = [
    path("", views.ImportApplicationChoiceView.as_view(), name="choice"),
    path("create/sanctions/", views.create_sanctions, name="create-sanctions"),
    path("create/firearms/oil/", views.create_oil, name="create-oil"),
    path("create/wood/quota/", views.create_wood_quota, name="create-wood-quota"),
    path("sanctions/", include("web.domains.case._import.sanctions.urls")),
    path("firearms/", include("web.domains.case._import.firearms.urls")),
    path("wood/", include("web.domains.case._import.wood.urls")),
]
