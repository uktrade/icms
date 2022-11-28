# flake8: noqa: F405
from .base import *

# Email settings for all non prod environments.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
AWS_SES_ACCESS_KEY_ID = ""
AWS_SES_SECRET_ACCESS_KEY = ""
AWS_SES_REGION_NAME = ""
AWS_SES_REGION_ENDPOINT = ""

# Email/phone contacts
EMAIL_FROM = env.str("ICMS_EMAIL_FROM", "enquiries.ilb@icms.trade.dev.uktrade.io")  # /PS-IGNORE
ILB_CONTACT_EMAIL = env.str(
    "ICMS_ILB_CONTACT_EMAIL", "enquiries.ilb@icms.trade.dev.uktrade.io"  # /PS-IGNORE
)
ILB_GSI_CONTACT_EMAIL = env.str(
    "ICMS_ILB_GSI_CONTACT_EMAIL", "enquiries.ilb.gsi@icms.trade.dev.uktrade.io"  # /PS-IGNORE
)
ILB_CONTACT_PHONE = env.str("ICMS_ILB_CONTACT_PHONE", "N/A")
ICMS_FIREARMS_HOMEOFFICE_EMAIL = env.str(
    "ICMS_FIREARMS_HOMEOFFICE_EMAIL", "firearms-homeoffice@example.com"  # /PS-IGNORE
)
ICMS_CFS_HSE_EMAIL = env.str("ICMS_CFS_HSE_EMAIL", "HSE@example.com")  # /PS-IGNORE
ICMS_GMP_BEIS_EMAIL = env.str("ICMS_GMP_BEIS_EMAIL", "BEIS@example.com")  # /PS-IGNORE

# Override secure cookies to use playwright in non-prod environments
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
