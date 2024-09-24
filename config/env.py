import os

import dj_database_url
from dbt_copilot_python.database import database_url_from_env
from dbt_copilot_python.network import setup_allowed_hosts
from dbt_copilot_python.utility import is_copilot
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .cf_env import CloudFoundryEnvironment


class DBTPlatformEnvironment(BaseSettings):
    """Class holding all environment variables for ICMS.

    Environment variables all have a prefix of "ICMS_"
    e.g. ICMS_STAFF_SSO_ENABLED == DBTPlatformEnvironment.staff_sso_enabled
    """

    model_config = SettingsConfigDict(
        env_prefix="ICMS_",
        extra="ignore",
        validate_default=False,
    )

    # Build step doesn't have "ICMS_" prefix
    build_step: bool = Field(alias="build_step", default=False)

    app_env: str
    secret_key: str
    allowed_hosts: list[str]
    debug: bool = False

    # S3 env vars
    aws_region: str = Field(alias="aws_region", default="")
    aws_storage_bucket_name: str = Field(alias="aws_storage_bucket_name", default="")

    # Redis env vars
    celery_broker_url: str = Field(alias="celery_broker_url", default="")

    # Staff SSO
    staff_sso_enabled: bool
    staff_sso_authbroker_url: str
    staff_sso_authbroker_client_id: str
    staff_sso_authbroker_client_secret: str
    staff_sso_authbroker_staff_sso_scope: str
    staff_sso_authbroker_anonymous_paths: list[str]
    staff_sso_authbroker_anonymous_url_names: list[str]

    # GOV.UK One Login
    gov_uk_one_login_enabled: bool
    gov_uk_one_login_openid_config_url: str
    gov_uk_one_login_scope: str
    gov_uk_one_login_importer_client_id: str
    gov_uk_one_login_importer_client_secret: str
    gov_uk_one_login_exporter_client_id: str
    gov_uk_one_login_exporter_client_secret: str
    gov_uk_one_login_get_client_config_path: str = "web.auth.utils"
    gov_uk_one_login_authentication_level_override: str = ""

    # GOV.UK Notify to send/receive emails (which are implemented using gov notify)
    gov_notify_api_key: str
    email_backend: str
    mail_task_rate_limit: str
    mail_task_retry_jitter: bool
    mail_task_max_retries: int
    # Your email address (used to test GOV.UK Notify)
    # Need to have registered with GOV Notify and have been invited to the ICMS project
    send_all_emails_to: list[str]

    # Email/phone contacts
    ilb_contact_email: str
    ilb_gsi_contact_email: str
    ilb_contact_phone: str
    ilb_contact_name: str
    ilb_contact_address: str
    firearms_homeoffice_email: str
    cfs_hse_email: str
    gmp_beis_email: str
    sanctions_email: str

    # Anti-virus django-chunk-s3-av-upload-handlers settings
    # https://github.com/uktrade/django-chunk-s3-av-upload-handlers#clamav
    # Values stored in Vault.
    clam_av_username: str
    clam_av_password: str
    clam_av_domain: str

    # Age in seconds
    django_session_cookie_age: int = 60 * 60

    # Bypass chief
    allow_bypass_chief_never_enable_in_prod: bool = False

    address_api_key: str = ""
    silenced_system_checks: list[str] = []

    send_licence_to_chief: bool
    icms_hmrc_domain: str
    icms_hmrc_update_licence_endpoint: str
    hawk_auth_id: str
    hawk_auth_key: str

    # Data migration - Section has defaults as they are only set in production
    allow_data_migration: bool
    v1_replica_user: str = ""
    v1_replica_password: str = ""
    v1_replica_dsn: str = ""
    prod_user: str = ""
    prod_password: str = ""
    data_migration_email_domain_exclude: str = ""

    workbasket_per_page: int = 100
    set_inactive_app_types_active: bool = False
    show_db_queries: bool = False
    show_debug_toolbar: bool = False

    companies_house_domain: str = "https://api.companieshouse.gov.uk/"
    companies_house_token: str

    sentry_enabled: bool = False
    sentry_dsn: str = ""
    sentry_environment: str = Field(alias="sentry_environment", default="")

    # Redis settings
    local_redis_url: str = "redis://redis:6379"

    # S3 endpoint URL
    local_aws_s3_endpoint_url: str = "http://localstack:4566/"

    # celery settings
    celery_task_always_eager: bool = False
    celery_eager_propagates_exceptions: bool = False

    # Site URL management
    caseworker_site_url: str
    importer_site_url: str
    exporter_site_url: str

    # CSP settings
    csp_report_only: bool = True
    csp_report_uri: list[str] | None = None

    # PDF signature certificate stuff
    p12_signature_base_64: str = ""
    p12_signature_password: str = ""

    # Google Analytics
    gtm_enabled: bool = True
    gtm_caseworker_container_id: str = ""
    gtm_importer_container_id: str = ""
    gtm_exporter_container_id: str = ""

    # Testing
    # Flag to decide if we want to save the PDFs generated as part of the visual regression tests - useful for debugging
    save_generated_pdfs: bool = True

    def get_allowed_hosts(self) -> list[str]:
        if self.build_step:
            return self.allowed_hosts

        # Makes an external network request so only call when running on DBT Platform
        return setup_allowed_hosts(self.allowed_hosts)

    def get_database_config(self) -> dict:
        if self.build_step:
            return {"default": {}}

        return {
            "default": dj_database_url.parse(database_url_from_env("DATABASE_CREDENTIALS")),
        }

    def get_s3_bucket_config(self) -> dict:
        """Return s3 bucket config that matches keys used in CF"""

        if self.build_step:
            return {"aws_region": "", "bucket_name": ""}

        return {"aws_region": self.aws_region, "bucket_name": self.aws_storage_bucket_name}

    def get_redis_url(self) -> str:
        if self.build_step:
            return ""

        return self.celery_broker_url


if is_copilot():
    if "BUILD_STEP" in os.environ:
        # When building use the fake settings in .env.circleci
        env: DBTPlatformEnvironment | CloudFoundryEnvironment = DBTPlatformEnvironment(
            _env_file=".env.circleci", _env_file_encoding="utf-8"
        )  # type:ignore[call-arg]
    else:
        # When deployed read values from environment variables
        env = DBTPlatformEnvironment()  # type:ignore[call-arg]
else:
    # Cloud Foundry environment
    env = CloudFoundryEnvironment()  # type:ignore[call-arg]
