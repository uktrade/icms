from django.urls import re_path

from web.domains.case.access.approval.views import (
    management_access_approval,
    management_access_approval_withdraw,
    take_ownership_approval,
    release_ownership_approval,
    case_approval_respond,
)


urlpatterns = [
    # approval request for admin
    re_path(
        "^case/(?P<pk>[0-9]+)/(?P<entity>importer|exporter)/approval-request/$",
        management_access_approval,
        name="case-management-access-approval",
    ),
    re_path(
        "^case/(?P<application_pk>[0-9]+)/(?P<entity>importer|exporter)/approval-request/(?P<approval_request_pk>[0-9]+)/withdraw/$",
        management_access_approval_withdraw,
        name="case-management-approval-request-withdraw",
    ),
    # approval request for importer/exporter contacts
    re_path(
        "case/(?P<pk>[0-9]+)/(?P<entity>importer|exporter)/take_ownership/$",
        take_ownership_approval,
        name="case-approval-take-ownership",
    ),
    re_path(
        "case/(?P<pk>[0-9]+)/(?P<entity>importer|exporter)/release_ownership/$",
        release_ownership_approval,
        name="case-approval-release-ownership",
    ),
    re_path(
        "case/(?P<application_pk>[0-9]+)/(?P<entity>importer|exporter)/approval-request/(?P<approval_request_pk>[0-9]+)/$",
        case_approval_respond,
        name="case-approval-respond",
    ),
]
