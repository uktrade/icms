"""icms URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from web.admin import icms_admin_site

# Custom 403 handler to send process_error exceptions to sentry
handler403 = "web.views.handler403_capture_process_error_view"

urlpatterns = [
    #
    # ICMS urls
    path("", include("web.urls")),
]


if settings.IS_PRIVATE_APP:
    urlpatterns += [
        #
        # Django Admin Site (superuser admin site)
        path("admin/", admin.site.urls),
        #
        # ICMS Admin site (Restricted admin site)
        path("icms-admin/", icms_admin_site.urls),
    ]


if settings.SHOW_DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
