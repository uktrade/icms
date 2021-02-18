import environ

from .base import *  # NOQA”

env = environ.Env()

ALLOWED_HOSTS = env.list("ICMS_ALLOWED_HOSTS", default=["localhost", "web"])
DEBUG = env.bool("ICMS_DEBUG", True)

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {"default": env.db("DATABASE_URL", "postgres://postgres:password@db:5432/postgres")}

#  Google recaptcha. Using test keys on localhost
RECAPTCHA_PUBLIC_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_PRIVATE_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]

# getAddress.io api key
ADDRESS_API_KEY = env.str("ICMS_ADDRESS_API_KEY", default="")

# used in email content
ILB_CONTACT_EMAIL = env.str("ICMS_ILB_CONTACT_EMAIL", "enquiries.ilb@icms.trade.dev.uktrade.io")
ILB_CONTACT_PHONE = env.str("ICMS_ILB_CONTACT_PHONE", "N/A")
