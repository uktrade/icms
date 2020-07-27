from django.urls import include, path

from web.flows import ApprovalRequestFlow, ExporterAccessRequestFlow, ImporterAccessRequestFlow
from web.viewflow.viewset import FlowViewSet

from ..fir.urls import fir_parent_urls
from . import views

importer_access_request_urls = FlowViewSet(ImporterAccessRequestFlow).urls
exporter_access_request_urls = FlowViewSet(ExporterAccessRequestFlow).urls
approval_request_urls = FlowViewSet(ApprovalRequestFlow).urls

# Add fir urls to both flows
importer_access_request_urls.extend(fir_parent_urls)
exporter_access_request_urls.extend(fir_parent_urls)

app_name = "access"


urlpatterns = [
    path("importer/", include((importer_access_request_urls, "importer"))),
    path("exporter/", include((exporter_access_request_urls, "exporter"))),
    path("approval/", include((approval_request_urls, "approval"))),
    path("requested/", views.AccessRequestCreatedView.as_view(), name="requested"),
]
