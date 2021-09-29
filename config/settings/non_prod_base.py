import environ

from .base import *  # NOQA”

env = environ.Env()

ALLOWED_HOSTS = env.list("ICMS_ALLOWED_HOSTS", default=["localhost", "web"])
DEBUG = env.bool("ICMS_DEBUG", True)
SHOW_DB_QUERIES = env.bool("SHOW_DB_QUERIES", False)

if SHOW_DB_QUERIES:
    MIDDLEWARE += ["web.middleware.common.DBQueriesMiddleware"]  # noqa: F405

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {"default": env.db("DATABASE_URL", "postgres://postgres:password@db:5432/postgres")}

#  Google recaptcha. Using test keys on localhost
RECAPTCHA_PUBLIC_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_PRIVATE_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]

# getAddress.io api key
ADDRESS_API_KEY = env.str("ICMS_ADDRESS_API_KEY", default="")

# Email/phone contacts
ILB_CONTACT_EMAIL = env.str("ICMS_ILB_CONTACT_EMAIL", "enquiries.ilb@icms.trade.dev.uktrade.io")
ILB_GSI_CONTACT_EMAIL = env.str(
    "ICMS_ILB_GSI_CONTACT_EMAIL", "enquiries.ilb.gsi@icms.trade.dev.uktrade.io"
)
ILB_CONTACT_PHONE = env.str("ICMS_ILB_CONTACT_PHONE", "N/A")
ICMS_FIREARMS_HOMEOFFICE_EMAIL = env.str(
    "ICMS_FIREARMS_HOMEOFFICE_EMAIL", "firearms-homeoffice@example.com"
)
ICMS_CFS_HSE_EMAIL = env.str("ICMS_CFS_HSE_EMAIL", "HSE@example.com")
ICMS_GMP_BEIS_EMAIL = env.str("ICMS_GMP_BEIS_EMAIL", "BEIS@example.com")

DEBUG_SHOW_ALL_WORKBASKET_ROWS = env.bool("DEBUG_SHOW_ALL_WORKBASKET_ROWS", True)

# for https://github.com/uktrade/django-chunk-s3-av-upload-handlers
AWS_REGION = "eu-west-2"
AWS_ACCESS_KEY_ID = "dev"
AWS_SECRET_ACCESS_KEY = "bar"
AWS_STORAGE_BUCKET_NAME = "icms.local"
AWS_S3_ENDPOINT_URL = "http://localstack:4572/"
