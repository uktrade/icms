from django.core.management import call_command

from .add_application_type_data import (
    add_export_application_type_data,
    add_import_application_type_data,
    add_import_application_type_endorsements,
)
from .add_case_email_data import add_nuclear_material_data, add_sanction_data
from .add_commodity_group_usage_data import add_usage_data
from .add_constabulary_data import add_constabulary_data
from .add_email_data import (
    add_gov_notify_templates,
    add_user_management_email_templates,
    archive_database_email_templates,
    update_database_email_templates,
)
from .add_fa_data import add_firearms_act_data
from .add_template_data import (
    add_cfs_declaration_template_countries,
    add_cfs_schedule_data,
    add_schedule_translation_templates,
)


def load_app_test_data():
    call_command("set_icms_sites")
    call_command("loaddata", "overseas_regions")
    call_command("loaddata", "country")
    call_command("loaddata", "country_groups")
    call_command("loaddata", "country_translation_set")
    call_command("loaddata", "country_translation")
    call_command("loaddata", "templates")
    add_cfs_schedule_data()
    add_cfs_declaration_template_countries()
    add_schedule_translation_templates()
    add_export_application_type_data()
    add_import_application_type_data()
    add_import_application_type_endorsements()
    call_command("loaddata", "units")
    call_command("loaddata", "commodity_types")
    call_command("loaddata", "commodities")
    call_command("loaddata", "commodity_groups")
    add_usage_data()
    add_constabulary_data()
    add_firearms_act_data()
    call_command("loaddata", "obsolete_calibre")
    call_command("loaddata", "product_legislations")
    add_sanction_data()
    add_nuclear_material_data()
    add_user_management_email_templates()
    update_database_email_templates()
    archive_database_email_templates()
    add_gov_notify_templates()
    # TODO: Revisit in ECIL-601 (all ecil_xxx commands and fixture data should be data migrations)
    call_command("ECIL_657_add_dfl_country_groups")
    call_command("ECIL_647_add_nuclear_material_app")
    call_command("ECIL_652_add_nuclear_commodities")
