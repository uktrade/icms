from .views import (
    AccessibilityStatementView,
    LoginRequiredSelect2AutoResponseView,
    ModelCreateView,
    ModelDetailView,
    ModelFilterView,
    ModelUpdateView,
    RedirectBaseDomainView,
    V1ToV2ServiceRenameView,
    cookie_consent_view,
    handler403_capture_process_error_view,
    home,
    login_start_view,
    logout_view,
)
from .views_healthcheck import health_check

__all__ = [
    "AccessibilityStatementView",
    "LoginRequiredSelect2AutoResponseView",
    "ModelCreateView",
    "ModelDetailView",
    "ModelFilterView",
    "ModelUpdateView",
    "RedirectBaseDomainView",
    "V1ToV2ServiceRenameView",
    "home",
    "login_start_view",
    "logout_view",
    "health_check",
    "cookie_consent_view",
    "handler403_capture_process_error_view",
]
