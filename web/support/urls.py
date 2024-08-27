from django.urls import path

from .views import (
    AccessibilityStatementView,
    SupportLandingView,
    ValidateSignatureV1View,
    ValidateSignatureV2View,
    ValidateSignatureView,
)

app_name = "support"

urlpatterns = [
    path(
        "",
        SupportLandingView.as_view(),
        name="landing",
    ),
    path(
        "accessibility-statement/",
        AccessibilityStatementView.as_view(),
        name="accessibility-statement",
    ),
    path(
        "validate-signature/",
        ValidateSignatureView.as_view(),
        name="validate-signature",
    ),
    path(
        "validate-signature/v1/",
        ValidateSignatureV1View.as_view(),
        name="validate-signature-v1",
    ),
    path(
        "validate-signature/v2/",
        ValidateSignatureV2View.as_view(),
        name="validate-signature-v2",
    ),
]
