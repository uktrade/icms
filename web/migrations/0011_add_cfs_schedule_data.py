from django.db import migrations


def add_cfs_schedule_data(apps, schema_editor):
    Template = apps.get_model("web", "Template")
    Para = apps.get_model("web", "CFSScheduleParagraph")

    t = Template.objects.create(
        template_name="CFS Schedule template",
        template_type="CFS_SCHEDULE",
        application_domain="CA",
    )

    Para.objects.bulk_create(
        [
            Para(
                template=t,
                order=1,
                name="SCHEDULE_HEADER",
                content="Schedule to Certificate of Free Sale",
            ),
            Para(
                template=t,
                order=2,
                name="SCHEDULE_INTRODUCTION",
                content="[[EXPORTER_NAME]], of [[EXPORTER_ADDRESS_FLAT]] has made the following legal declaration in relation to the products listed in this schedule:",
            ),
            Para(template=t, order=3, name="IS_MANUFACTURER", content="I am the manufacturer."),
            Para(
                template=t,
                order=4,
                name="IS_NOT_MANUFACTURER",
                content="I am not the manufacturer.",
            ),
            Para(
                template=t,
                order=5,
                name="EU_COSMETICS_RESPONSIBLE_PERSON",
                content="I am the responsible person as defined by the EU Cosmetics Regulation 1223/2009 and I am the person responsible for ensuring that the products listed in this schedule meet the safety requirements set out in the EU Cosmetics Regulation 1223/2009",
            ),
            Para(
                template=t,
                order=6,
                name="LEGISLATION_STATEMENT",
                content="I certify that these products meet the safety requirements set out under UK and EU legislation, specifically:",
            ),
            Para(
                template=t,
                order=7,
                name="ELIGIBILITY_ON_SALE",
                content="These products are currently sold on the EU market.",
            ),
            Para(
                template=t,
                order=8,
                name="ELIGIBILITY_MAY_BE_SOLD",
                content="These products meet the product safety requirements to be sold on the EU market.",
            ),
            Para(
                template=t,
                order=9,
                name="GOOD_MANUFACTURING_PRACTICE",
                content="These products are manufactured in accordance with the Good Manufacturing Practice standards set out in UK and EU law",
            ),
            Para(
                template=t,
                order=10,
                name="COUNTRY_OF_MAN_STATEMENT",
                content="The products were manufactured in [[COUNTRY_OF_MANUFACTURE]]",
            ),
            Para(
                template=t,
                order=11,
                name="COUNTRY_OF_MAN_STATEMENT_WITH_NAME",
                content="The products were manufactured in [[COUNTRY_OF_MANUFACTURE]] by [[MANUFACTURED_AT_NAME]]",
            ),
            Para(
                template=t,
                order=12,
                name="COUNTRY_OF_MAN_STATEMENT_WITH_NAME_AND_ADDRESS",
                content="The products were manufactured in [[COUNTRY_OF_MANUFACTURE]] by [[MANUFACTURED_AT_NAME]] at [[MANUFACTURED_AT_ADDRESS_FLAT]]",
            ),
            Para(template=t, order=13, name="PRODUCTS", content="Products"),
        ]
    )


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_cfs_schedule_data),
    ]
