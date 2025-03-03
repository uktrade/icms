from typing import Any, TypeAlias

from pydantic import BaseModel

from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
)


class CGSFrontendJinjaTemplateContext(BaseModel):
    """Available context to set for the base template.

    Template can be viewed here:
    site-packages/govuk_frontend_jinja/templates/template.html
    """

    pageTitleLang: str | None = None
    pageTitle: str | None = None
    themeColor: str | None = None
    assetPath: str | None = None
    opengraphImageUrl: str | None = None
    bodyClasses: str | None = None
    bodyAttributes: str | None = None
    cspNonce: Any = None
    containerClasses: str | None = None
    mainClasses: str | None = None
    mainLang: str | None = None


EXPORT_APPLICATION: TypeAlias = (
    CertificateOfFreeSaleApplication
    | CertificateOfGoodManufacturingPracticeApplication
    | CertificateOfManufactureApplication
)
