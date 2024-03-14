from django.db.models import QuerySet

from web.domains.cat.utils import (
    get_user_templates,
    template_in_user_templates,
    user_can_edit_template,
)
from web.models import CertificateApplicationTemplate, ExportApplicationType, User
from web.permissions import organisation_add_contact

CAT_SS = CertificateApplicationTemplate.SharingStatuses


def test_get_user_templates(exporter, exporter_one_contact, exporter_two_contact):
    exporter_one_contact_two = User.objects.create(
        email="exporter_one_c2@example.com",  # /PS-IGNORE
        first_name="E1_C2",
        last_name="lastname",  # /PS-IGNORE
    )
    organisation_add_contact(exporter, exporter_one_contact_two)

    # Add Templates for exporter_one_contact
    _create_cat("E1_C1_cat_1_editable", exporter_one_contact, CAT_SS.EDIT)
    _create_cat("E1_C1_cat_2_private", exporter_one_contact, CAT_SS.PRIVATE)
    template = _create_cat("E1_C1_cat_3_private_inactive", exporter_one_contact, CAT_SS.PRIVATE)
    template.is_active = False
    template.save()

    # Add Templates for exporter_one_contact_two
    _create_cat("E1_C2_cat_1_editable", exporter_one_contact_two, CAT_SS.EDIT)
    _create_cat("E1_C2_cat_2_viewable", exporter_one_contact_two, CAT_SS.VIEW)

    # Add Templates for exporter_two_contact
    _create_cat("E2_C1_cat_1_editable", exporter_two_contact, CAT_SS.EDIT)
    _create_cat("E2_C1_cat_2_editable", exporter_two_contact, CAT_SS.EDIT)

    # Test templates exporter_one_contact can see
    _assert_templates_seen(
        get_user_templates(exporter_one_contact),
        "E1_C1_cat_1_editable",
        "E1_C1_cat_2_private",
        "E1_C2_cat_1_editable",
        "E1_C2_cat_2_viewable",
    )
    _assert_templates_seen(
        get_user_templates(exporter_one_contact, include_inactive=True),
        "E1_C1_cat_1_editable",
        "E1_C1_cat_2_private",
        "E1_C1_cat_3_private_inactive",
        "E1_C2_cat_1_editable",
        "E1_C2_cat_2_viewable",
    )

    # Test templates exporter_one_contact_two can see
    _assert_templates_seen(
        get_user_templates(exporter_one_contact_two),
        "E1_C2_cat_1_editable",
        "E1_C2_cat_2_viewable",
        "E1_C1_cat_1_editable",
    )

    # Test templates exporter_two_contact can see
    _assert_templates_seen(
        get_user_templates(exporter_two_contact), "E2_C1_cat_1_editable", "E2_C1_cat_2_editable"
    )


def test_template_in_user_templates(exporter_one_contact, exporter_two_contact):
    template_1 = _create_cat("template_1", exporter_one_contact, CAT_SS.EDIT)
    template_2 = _create_cat("template_2", exporter_two_contact, CAT_SS.EDIT)
    template_3 = _create_cat("template_3", exporter_two_contact, CAT_SS.EDIT)
    template_3.is_active = False
    template_3.save()

    assert template_in_user_templates(exporter_one_contact, template_1)
    assert not template_in_user_templates(exporter_one_contact, template_2)
    assert not template_in_user_templates(exporter_one_contact, template_3)
    assert not template_in_user_templates(exporter_one_contact, template_3, include_inactive=True)

    assert not template_in_user_templates(exporter_two_contact, template_1)
    assert template_in_user_templates(exporter_two_contact, template_2)
    assert not template_in_user_templates(exporter_two_contact, template_3)
    assert template_in_user_templates(exporter_two_contact, template_3, include_inactive=True)


def test_user_can_edit_template(exporter, exporter_one_contact):
    exporter_one_contact_two = User.objects.create(
        email="exporter_one_c2@example.com",  # /PS-IGNORE
        first_name="E1_C2",
        last_name="lastname",  # /PS-IGNORE
    )
    organisation_add_contact(exporter, exporter_one_contact_two)

    template_1 = _create_cat("template_1", exporter_one_contact, CAT_SS.EDIT)
    template_2 = _create_cat("template_1", exporter_one_contact, CAT_SS.VIEW)
    template_3 = _create_cat("template_1", exporter_one_contact, CAT_SS.PRIVATE)

    assert user_can_edit_template(exporter_one_contact, template_1)
    assert user_can_edit_template(exporter_one_contact, template_2)
    assert user_can_edit_template(exporter_one_contact, template_3)

    assert user_can_edit_template(exporter_one_contact_two, template_1)
    assert not user_can_edit_template(exporter_one_contact_two, template_2)
    assert not user_can_edit_template(exporter_one_contact_two, template_3)


def _create_cat(
    name,
    owner,
    sharing,
    *,
    description="Template Description",
    application_type=ExportApplicationType.Types.FREE_SALE,
):

    return CertificateApplicationTemplate.objects.create(
        name=name,
        description=description,
        application_type=application_type,
        sharing=sharing,
        owner=owner,
    )


def _assert_templates_seen(
    templates: QuerySet[CertificateApplicationTemplate], *expected_templates: str
) -> None:
    actual_templates = sorted(templates.values_list("name", flat=True))

    assert sorted(expected_templates) == actual_templates
