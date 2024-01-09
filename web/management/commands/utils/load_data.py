from .add_application_type_data import (
    add_export_application_type_data,
    add_import_application_type_data,
    add_import_application_type_endorsements,
)
from .add_commodity_data import (
    add_commodities,
    add_commodities_to_commodity_groups,
    add_commodity_groups,
    add_commodity_types,
    add_units,
)
from .add_commodity_group_usage_data import add_usage_data
from .add_constabulary_data import add_constabulary_data
from .add_country_data import (
    add_country_translation,
    add_country_translation_set,
    load_country_data,
    load_country_group_data,
)
from .add_email_template_data import add_email_gov_notify_templates
from .add_product_legislation_data import add_product_legislation_data
from .add_reports_data import add_reports
from .add_sanction_data import add_sanction_data
from .add_template_data import (
    add_cfs_declaration_templates,
    add_cfs_schedule_data,
    add_declaration_templates,
    add_email_templates,
    add_endorsement_templates,
    add_letter_fragment_templates,
    add_letter_templates,
    add_schedule_translation_templates,
)


def load_app_test_data():
    load_country_data()
    load_country_group_data()
    add_country_translation_set()
    add_country_translation()
    add_cfs_schedule_data()
    add_cfs_declaration_templates()
    add_schedule_translation_templates()
    add_declaration_templates()
    add_endorsement_templates()
    add_email_templates()
    add_letter_templates()
    add_letter_fragment_templates()
    add_export_application_type_data()
    add_import_application_type_data()
    add_import_application_type_endorsements()
    add_units()
    add_commodity_types()
    add_commodity_groups()
    add_commodities()
    add_commodities_to_commodity_groups()
    add_usage_data()
    add_constabulary_data()
    add_product_legislation_data()
    add_sanction_data()
    add_email_gov_notify_templates()
    add_reports()
