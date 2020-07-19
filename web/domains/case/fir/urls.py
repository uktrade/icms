from django.urls import include, path

from web.viewflow.viewset import FlowViewSet

from .flows import FurtherInformationRequestFlow
from . import views

futher_information_request_urls = FlowViewSet(FurtherInformationRequestFlow).urls

app_name = "fir"

urlpatterns = [
    path("", include(futher_information_request_urls)),
]

# Generic new FIR and FIR list pages to be included with parent processes
# that has parallel FIR flows
fir_parent_urls = [
    path(
        "<parent_process_pk>/fir/request/",
        views.FurtherInformationRequestStartView.as_view(),
        name="fir-new",
    ),
    path(
        "<parent_process_pk>/fir/list/",
        views.FurtherInformationRequestListView.as_view(),
        name="fir-list",
    ),
]
