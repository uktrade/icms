from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, PostgresDsn, TypeAdapter
from pydantic.functional_validators import PlainValidator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Convert the database_url to a PostgresDsn instance
def validate_postgres_dsn_str(val) -> PostgresDsn:
    return TypeAdapter(PostgresDsn).validate_python(val)


CFPostgresDSN = Annotated[PostgresDsn, PlainValidator(validate_postgres_dsn_str)]


class VCAPServices(BaseModel):
    model_config = ConfigDict(extra="ignore")

    postgres: list[dict[str, Any]]
    redis: list[dict[str, Any]]
    user_provided: list[dict[str, Any]] = Field(alias="user-provided")
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


class Environment(BaseSettings):
    """Class holding all environment variables for ICMS.

    Instance attributes are matched to environment variables by name (ignoring case).
    e.g. Environment.app_env loads and validates the APP_ENV environment variable.
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
    database_url: CFPostgresDSN

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

    # Cloud Foundry Environment Variables
    vcap_services: VCAPServices | None = None
    vcap_application: VCAPApplication | None = None

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


env: Environment = Environment()  # type:ignore[call-arg]
