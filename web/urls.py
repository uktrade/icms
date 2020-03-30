from django.urls import include, path, register_converter

from web.domains.workbasket.views import take_ownership, workbasket

from . import converters
from web.domains.case.access.views import (AccessRequestCreatedView,
                                           AccessRequestFirView,
                                           LinkImporterView, LinkExporterView)
from web.domains.mailshot.views import MailshotListView

from .flows import AccessRequestFlow
from .views import home

register_converter(converters.NegativeIntConverter, 'negint')

urlpatterns = [
    path('', include('web.auth.urls')),
    path('home/', home, name='home'),
    path('', include('web.domains.workbasket.urls')),
    path('', include('web.domains.user.urls')),
    path('', include('web.domains.template.urls')),
    path('', include('web.domains.team.urls')),
    path('', include('web.domains.constabulary.urls')),
    path('', include('web.domains.commodity.urls')),
    path('', include('web.domains.country.urls')),
    path('', include('web.domains.legislation.urls')),
    path('', include('web.domains.firearms.urls')),
    path('', include('web.domains.importer.urls')),
    path('', include('web.domains.exporter.urls')),
    path('', include('web.domains.case.access.urls')),
    path('', include('web.domains.application._import.urls')),
    path('', include('web.domains.mailshot.urls')),
]
