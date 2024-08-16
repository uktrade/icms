from web.models import CFSScheduleParagraph, Country, CountryTranslationSet, Template


def add_cfs_schedule_data():
    t = Template.objects.get(
        template_type="CFS_SCHEDULE",
        template_code="CFS_SCHEDULE_ENGLISH",
        application_domain="CA",
    )

    CFSScheduleParagraph.objects.bulk_create(
        [
            CFSScheduleParagraph(
                template=t,
                order=1,
                name="SCHEDULE_HEADER",
                content="Schedule to Certificate of Free Sale",
            ),
            CFSScheduleParagraph(
                template=t,
                order=2,
                name="SCHEDULE_INTRODUCTION",
                content="[[EXPORTER_NAME]], of [[EXPORTER_ADDRESS_FLAT]] has made the following legal declaration in relation to the products listed in this schedule:",
            ),
            CFSScheduleParagraph(
                template=t, order=3, name="IS_MANUFACTURER", content="I am the manufacturer."
            ),
            CFSScheduleParagraph(
                template=t,
                order=4,
                name="IS_NOT_MANUFACTURER",
                content="I am not the manufacturer.",
            ),
            CFSScheduleParagraph(
                template=t,
                order=5,
                name="EU_COSMETICS_RESPONSIBLE_PERSON",
                content="I am the responsible person as defined by the EU Cosmetics Regulation 1223/2009 and I am the person responsible for ensuring that the products listed in this schedule meet the safety requirements set out in the EU Cosmetics Regulation 1223/2009.",
            ),
            CFSScheduleParagraph(
                template=t,
                order=6,
                name="EU_COSMETICS_RESPONSIBLE_PERSON_NI",
                content="I am the responsible person as defined by Regulation (EC) No 1223/2009 of the European Parliament and of the Council of 30 November 2009 on cosmetic products and Cosmetic Regulation No 1223/2009 as applicable in NI. I am the person responsible for ensuring that the products listed in this schedule meet the safety requirements set out in the Regulations.",
            ),
            CFSScheduleParagraph(
                template=t,
                order=7,
                name="LEGISLATION_STATEMENT",
                content="I certify that these products meet the safety requirements set out under UK and EU legislation, specifically:",
            ),
            CFSScheduleParagraph(
                template=t,
                order=8,
                name="ELIGIBILITY_ON_SALE",
                content="These products are currently sold on the EU market.",
            ),
            CFSScheduleParagraph(
                template=t,
                order=9,
                name="ELIGIBILITY_MAY_BE_SOLD",
                content="These products meet the product safety requirements to be sold on the EU market.",
            ),
            CFSScheduleParagraph(
                template=t,
                order=10,
                name="GOOD_MANUFACTURING_PRACTICE",
                content="These products are manufactured in accordance with the Good Manufacturing Practice standards set out in UK and EU law",
            ),
            CFSScheduleParagraph(
                template=t,
                order=11,
                name="GOOD_MANUFACTURING_PRACTICE_NI",
                content="These products are manufactured in accordance with the Good Manufacturing Practice standards set out in UK or EU law where applicable",
            ),
            CFSScheduleParagraph(
                template=t,
                order=12,
                name="COUNTRY_OF_MAN_STATEMENT",
                content="The products were manufactured in [[COUNTRY_OF_MANUFACTURE]]",
            ),
            CFSScheduleParagraph(
                template=t,
                order=13,
                name="COUNTRY_OF_MAN_STATEMENT_WITH_NAME",
                content="The products were manufactured in [[COUNTRY_OF_MANUFACTURE]] by [[MANUFACTURED_AT_NAME]]",
            ),
            CFSScheduleParagraph(
                template=t,
                order=14,
                name="COUNTRY_OF_MAN_STATEMENT_WITH_NAME_AND_ADDRESS",
                content="The products were manufactured in [[COUNTRY_OF_MANUFACTURE]] by [[MANUFACTURED_AT_NAME]] at [[MANUFACTURED_AT_ADDRESS_FLAT]]",
            ),
            CFSScheduleParagraph(template=t, order=15, name="PRODUCTS", content="Products"),
        ]
    )


def add_cfs_declaration_template_countries():
    spanish = Template.objects.get(
        template_name="Spanish", template_type="CFS_DECLARATION_TRANSLATION"
    )
    spanish.countries.add(
        *Country.objects.filter(
            name__in=[
                "Algeria",
                "Argentina",
                "Bolivia",
                "Chile",
                "Colombia",
                "Costa Rica",
                "Dominican Republic",
                "Ecuador",
                "El Salvador",
                "Guatemala",
                "Honduras",
                "Jamaica",
                "Mexico",
                "Nicaragua",
                "Panama",
                "Paraguay",
                "Peru",
                "Uruguay",
                "Venezuela",
            ]
        )
    )
    french = Template.objects.get(
        template_name="French", template_type="CFS_DECLARATION_TRANSLATION"
    )
    french.countries.add(*Country.objects.filter(name__in=["Algeria", "Tunisia"]))

    portuguese = Template.objects.get(
        template_name="Portuguese", template_type="CFS_DECLARATION_TRANSLATION"
    )
    portuguese.countries.add(*Country.objects.filter(name__in=["Brazil"]))

    russian = Template.objects.get(
        template_name="Russian",
        template_type="CFS_DECLARATION_TRANSLATION",
    )
    russian.countries.add(*Country.objects.filter(name__in=["Russian Federation"]))

    turkish = Template.objects.get(
        template_name="Turkish",
        template_type="CFS_DECLARATION_TRANSLATION",
    )
    turkish.countries.add(*Country.objects.filter(name__in=["Turkey"]))


def add_schedule_translation_templates():
    t = Template.objects.get(
        template_name="Spanish CFS Schedule",
        template_code="CFS_SCHEDULE_TRANSLATION",
        template_type="CFS_SCHEDULE_TRANSLATION",
        application_domain="CA",
        country_translation_set=CountryTranslationSet.objects.get(name="Spanish"),
    )

    t.countries.add(
        *Country.objects.filter(
            name__in=[
                "Argentina",
                "Bolivia",
                "Chile",
                "Colombia",
                "Costa Rica",
                "Dominican Republic",
                "Ecuador",
                "El Salvador",
                "Guatemala",
                "Honduras",
                "Jamaica",
                "Mexico",
                "Nicaragua",
                "Panama",
                "Paraguay",
                "Peru",
                "Uruguay",
                "Venezuela",
            ]
        )
    )

    CFSScheduleParagraph.objects.bulk_create(
        CFSScheduleParagraph(template=t, **data)
        for data in [
            {
                "order": 1,
                "name": "SCHEDULE_HEADER",
                "content": "Horario para el Certificado de Libre Venta",
            },
            {
                "order": 2,
                "name": "SCHEDULE_INTRODUCTION",
                "content": "[[EXPORTER_NAME]], de [[EXPORTER_ADDRESS_FLAT]] ha hecho la siguiente declaración legal en relación con los productos enumerados en este cronograma:",
            },
            {"order": 3, "name": "IS_MANUFACTURER", "content": "Yo soy el fabricante."},
            {"order": 4, "name": "IS_NOT_MANUFACTURER", "content": "No soy el fabricante."},
            {
                "order": 5,
                "name": "EU_COSMETICS_RESPONSIBLE_PERSON",
                "content": "Soy la persona responsable según lo definido por el Reglamento de cosméticos n. ° 1223/2009 según se aplique en GB. Soy la persona responsable de garantizar que los productos enumerados en este programa cumplan con los requisitos de seguridad establecidos en ese Reglamento.",
            },
            {
                "order": 6,
                "name": "LEGISLATION_STATEMENT",
                "content": "Certifico que estos productos cumplen con los requisitos de seguridad establecidos en esta legislación:",
            },
            {
                "order": 7,
                "name": "ELIGIBILITY_ON_SALE",
                "content": "Estos productos se venden actualmente en el mercado del Reino Unido.",
            },
            {
                "order": 8,
                "name": "ELIGIBILITY_MAY_BE_SOLD",
                "content": "Estos productos cumplen con los requisitos de seguridad de los productos para ser vendidos en el mercado del Reino Unido.",
            },
            {
                "order": 9,
                "name": "GOOD_MANUFACTURING_PRACTICE",
                "content": "Estos productos se fabrican de acuerdo con las normas de buenas prácticas de fabricación establecidas en las leyes del Reino Unido",
            },
            {
                "order": 10,
                "name": "COUNTRY_OF_MAN_STATEMENT",
                "content": "Los productos fueron fabricados en [[COUNTRY_OF_MANUFACTURE]]",
            },
            {
                "order": 11,
                "name": "COUNTRY_OF_MAN_STATEMENT_WITH_NAME",
                "content": "Los productos fueron fabricados en [[COUNTRY_OF_MANUFACTURE]] por [[MANUFACTURED_AT_NAME]]",
            },
            {
                "order": 12,
                "name": "COUNTRY_OF_MAN_STATEMENT_WITH_NAME_AND_ADDRESS",
                "content": "Los productos fueron fabricados en [[COUNTRY_OF_MANUFACTURE]] por [[MANUFACTURED_AT_NAME]] en [[MANUFACTURED_AT_ADDRESS_FLAT]]",
            },
            {"order": 13, "name": "PRODUCTS", "content": "Productos"},
            {
                "order": 14,
                "name": "EU_COSMETICS_RESPONSIBLE_PERSON_NI",
                "content": "Soy la persona responsable según lo definido por el Reglamento (CE) n. ° 1223/2009 del Parlamento Europeo y del Consejo de 30 de noviembre de 2009 sobre productos cosméticos y el Reglamento sobre cosméticos n. ° 1223/2009 según corresponda en NI. Soy la persona responsable de asegurar que los productos enumerados en este programa cumplan con los requisitos de seguridad establecidos en el Reglamento.",
            },
            {
                "order": 15,
                "name": "GOOD_MANUFACTURING_PRACTICE_NI",
                "content": "Estos productos se fabrican de acuerdo con las normas de buenas prácticas de fabricación establecidas en la legislación del Reino Unido o de la UE, cuando corresponda.",
            },
        ]
    )
