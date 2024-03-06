import os
from typing import Annotated, Any

import dj_database_url
from dbt_copilot_python.database import database_url_from_env
from dbt_copilot_python.network import setup_allowed_hosts
from dbt_copilot_python.utility import is_copilot
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PostgresDsn,
    TypeAdapter,
    computed_field,
)
from pydantic.functional_validators import PlainValidator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentBase(BaseSettings):
    """Class holding all environment variables for ICMS.

    Instance attributes are matched to environment variables by name (ignoring case).
    e.g. DBTPlatformEnvironment.app_env loads and validates the APP_ENV environment variable.
    """

    model_config = SettingsConfigDict(
        extra="ignore",
        validate_default=False,
    )

    # Start of Environment Variables
    app_env: str
    icms_secret_key: str
    icms_allowed_hosts: list[str]
    icms_debug: bool = False

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
    gov_uk_one_login_client_id: str
    gov_uk_one_login_client_secret: str
    gov_uk_one_login_scope: str
    gov_uk_one_login_openid_config_url: str

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
    icms_email_from: str
    icms_ilb_contact_email: str
    icms_ilb_gsi_contact_email: str
    icms_ilb_contact_phone: str
    icms_ilb_contact_name: str
    icms_ilb_contact_address: str
    icms_firearms_homeoffice_email: str
    icms_cfs_hse_email: str
    icms_gmp_beis_email: str

    # Anti-virus django-chunk-s3-av-upload-handlers settings
    # https://github.com/uktrade/django-chunk-s3-av-upload-handlers#clamav
    # Values stored in Vault.
    clam_av_username: str
    clam_av_password: str
    clam_av_domain: str

    # Age in seconds
    django_session_cookie_age: int = 60 * 30

    # related with drop_all_tables command
    allow_disastrous_data_drops_never_enable_in_prod: bool = False
    # Bypass chief
    allow_bypass_chief_never_enable_in_prod: bool = False

    icms_address_api_key: str = ""
    icms_silenced_system_checks: list[str] = []

    send_licence_to_chief: bool
    icms_hmrc_domain: str
    icms_hmrc_update_licence_endpoint: str
    hawk_auth_id: str
    hawk_auth_key: str

    # Data migration - Section has defaults as they are only set in production
    allow_data_migration: bool
    icms_v1_replica_user: str = ""
    icms_v1_replica_password: str = ""
    icms_v1_replica_dsn: str = ""
    icms_prod_user: str = ""
    icms_prod_password: str = ""
    data_migration_email_domain_exclude: str = ""

    workbasket_per_page: int = 100
    set_inactive_app_types_active: bool = False
    show_db_queries: bool = False
    show_debug_toolbar: bool = False

    # Only set in production
    elastic_apm_secret_token: str = ""
    elastic_apm_url: str = ""
    elastic_apm_environment: str = "development"
    elastic_apm_server_timeout: str = "20s"

    companies_house_domain: str = "https://api.companieshouse.gov.uk/"
    companies_house_token: str

    sentry_enabled: bool = False
    sentry_dsn: str = ""
    sentry_environment: str = ""

    # Redis settings
    local_redis_url: str = "redis://redis:6379"

    # S3 endpoint URL
    local_aws_s3_endpoint_url: str = "http://localstack:4566/"

    # celery settings
    celery_task_always_eager: bool = False
    celery_eager_propagates_exceptions: bool = False

    # local site URL management
    local_site_url: str = "http://web:8080/"

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

    @computed_field  # type: ignore[misc]
    @property
    def allowed_hosts(self) -> list[str]:
        raise NotImplementedError

    @computed_field  # type: ignore[misc]
    @property
    def database_config(self) -> dict:
        raise NotImplementedError

    @computed_field  # type: ignore[misc]
    @property
    def s3_bucket_config(self) -> dict:
        raise NotImplementedError

    @computed_field  # type: ignore[misc]
    @property
    def redis_url(self) -> str:
        raise NotImplementedError


# Convert the database_url to a PostgresDsn instance
def validate_postgres_dsn_str(val) -> PostgresDsn:
    return TypeAdapter(PostgresDsn).validate_python(val)


CFPostgresDSN = Annotated[PostgresDsn, PlainValidator(validate_postgres_dsn_str)]


class VCAPServices(BaseModel):
    model_config = ConfigDict(extra="ignore")

    postgres: list[dict[str, Any]]
    redis: list[dict[str, Any]]
    aws_s3_bucket: list[dict[str, Any]] = Field(alias="aws-s3-bucket")


class VCAPApplication(BaseModel):
    model_config = ConfigDict(extra="ignore")

    application_id: str
    application_name: str
    application_uris: list[str]
    cf_api: str
    limits: dict[str, Any]
    name: str
    organization_id: str
    organization_name: str
    space_id: str
    uris: list[str]


class CloudFoundryEnvironment(EnvironmentBase):
    database_url: CFPostgresDSN

    # Cloud Foundry Environment Variables
    vcap_services: VCAPServices | None = None
    vcap_application: VCAPApplication | None = None

    @computed_field  # type: ignore[misc]
    @property
    def allowed_hosts(self) -> list[str]:
        return self.icms_allowed_hosts

    @computed_field  # type: ignore[misc]
    @property
    def database_config(self) -> dict:
        return {"default": dj_database_url.parse(str(self.database_url))}

    @computed_field  # type: ignore[misc]
    @property
    def s3_bucket_config(self) -> dict:
        if self.vcap_services:
            app_bucket_creds = self.vcap_services.aws_s3_bucket[0]["credentials"]
        else:
            app_bucket_creds = {}

        return app_bucket_creds

    @computed_field  # type: ignore[misc]
    @property
    def redis_url(self) -> str:
        if self.vcap_services:
            return self.vcap_services.redis[0]["credentials"]["uri"]

        return self.local_redis_url


class DBTPlatformEnvironment(EnvironmentBase):
    build_step: bool = False

    # S3 env vars
    aws_region: str = ""
    aws_storage_bucket_name: str = ""

    # Redis env vars
    celery_broker_url: str = ""

    @computed_field  # type: ignore[misc]
    @property
    def allowed_hosts(self) -> list[str]:
        if self.build_step:
            return self.icms_allowed_hosts

        # Makes an external network request so only call when running on DBT Platform
        return setup_allowed_hosts(self.icms_allowed_hosts)

    @computed_field  # type: ignore[misc]
    @property
    def database_config(self) -> dict:
        if self.build_step:
            return {"default": {}}

        return {
            "default": dj_database_url.config(default=database_url_from_env("DATABASE_CREDENTIALS"))
        }

    @computed_field  # type: ignore[misc]
    @property
    def s3_bucket_config(self) -> dict:
        """Return s3 bucket config that matches keys used in CF"""

        if self.build_step:
            return {"aws_region": "", "bucket_name": ""}

        return {"aws_region": self.aws_region, "bucket_name": self.aws_storage_bucket_name}

    @computed_field  # type: ignore[misc]
    @property
    def redis_url(self) -> str:
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
    # Cloud Foundry environemnt
    env = CloudFoundryEnvironment()  # type:ignore[call-arg]
