from typing import Any

from web.types import AuthenticatedHttpRequest

from .types import CGSFrontendJinjaTemplateContext


def govuk_frontend_jinja_template(request: AuthenticatedHttpRequest) -> dict[str, Any]:
    """Context variables required by govuk_frontend_jinja/template.html"""

    required_gds_template_ctx = CGSFrontendJinjaTemplateContext(cspNonce=request.csp_nonce)

    return required_gds_template_ctx.model_dump(include={"cspNonce"})
