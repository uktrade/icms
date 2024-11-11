from django.conf import settings
from django.urls import re_path

from web.domains.case.access.approval.views import (
    close_access_approval,
    manage_access_approval,
    manage_access_approval_withdraw,
    release_ownership_access_approval,
    take_ownership_access_approval,
)

public_urls = [
    # approval request for importer/exporter contacts
    re_path(
        "case/(?P<approval_request_pk>[0-9]+)/(?P<entity>importer|exporter)/take_ownership/$",
        take_ownership_access_approval,
        name="case-approval-take-ownership",
    ),
    re_path(
        "case/(?P<approval_request_pk>[0-9]+)/(?P<entity>importer|exporter)/release_ownership/$",
        release_ownership_access_approval,
        name="case-approval-release-ownership",
    ),
    re_path(
        "case/(?P<access_request_pk>[0-9]+)/(?P<entity>importer|exporter)/approval-request/(?P<approval_request_pk>[0-9]+)/$",
        close_access_approval,
        name="case-approval-respond",
    ),
]

private_urls = [
    # approval request for admin
    re_path(
        "^case/(?P<access_request_pk>[0-9]+)/(?P<entity>importer|exporter)/approval-request/$",
        manage_access_approval,
        name="case-management-access-approval",
    ),
    re_path(
        "^case/(?P<access_request_pk>[0-9]+)/(?P<entity>importer|exporter)/approval-request/(?P<approval_request_pk>[0-9]+)/withdraw/$",
        manage_access_approval_withdraw,
        name="case-management-approval-request-withdraw",
    ),
]

if settings.INCLUDE_PRIVATE_URLS:
    urlpatterns = public_urls + private_urls
else:
    urlpatterns = public_urls
