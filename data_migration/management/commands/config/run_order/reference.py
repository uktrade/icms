from data_migration import models as dm
from data_migration import queries
from data_migration.management.commands._types import (
    M2M,
    QueryModel,
    source_target_list,
)
from web import models as web

ref_query_model = [
    QueryModel(queries.country, "country", dm.Country),
    QueryModel(queries.country_group, "country_group", dm.CountryGroup),
    QueryModel(queries.country_group_country, "country_group_country", dm.CountryGroupCountry),
    QueryModel(
        queries.country_translation_set, "country_translation_set", dm.CountryTranslationSet
    ),
    QueryModel(queries.country_translation, "country_translation", dm.CountryTranslation),
    QueryModel(queries.unit, "unit", dm.Unit),
    QueryModel(queries.commodity_type, "commodity_type", dm.CommodityType),
    QueryModel(queries.commodity_group, "commodity_group", dm.CommodityGroup),
    QueryModel(queries.commodity, "commodity", dm.Commodity),
    QueryModel(
        queries.commodity_group_commodity, "commodity_group_commodity", dm.CommodityGroupCommodity
    ),
    QueryModel(queries.template, "template", dm.Template),
    QueryModel(queries.cfs_paragraph, "cfs paragraph", dm.CFSScheduleParagraph),
    QueryModel(queries.template_country, "template country", dm.TemplateCountry),
    QueryModel(queries.ia_type, "ia_type", dm.ImportApplicationType),
    QueryModel(queries.endorsement_template, "endorsement template", dm.EndorsementTemplate),
    QueryModel(queries.usage, "usage", dm.Usage),
    QueryModel(queries.constabularies, "constabularies", dm.Constabulary),
    QueryModel(queries.obsolete_calibre_group, "obsolete_calibre_group", dm.ObsoleteCalibreGroup),
    QueryModel(queries.obsolete_calibre, "obsolete_calibre", dm.ObsoleteCalibre),
]

ref_source_target = source_target_list(
    [
        "Country",
        "CountryGroup",
        "CountryTranslationSet",
        "CountryTranslation",
        "Unit",
        "CommodityType",
        "CommodityGroup",
        "Commodity",
        "Template",
        "CFSScheduleParagraph",
        "ImportApplicationType",
        "Usage",
        "Constabulary",
        "ObsoleteCalibreGroup",
        "ObsoleteCalibre",
        "CaseNote",
        "CaseEmail",
        "UpdateRequest",
        "UniqueReference",
    ]
)

ref_m2m = [
    M2M(dm.CountryGroupCountry, web.CountryGroup, "countries"),
    M2M(dm.CommodityGroupCommodity, web.CommodityGroup, "commodities"),
    M2M(dm.TemplateCountry, web.Template, "countries"),
    M2M(dm.EndorsementTemplate, web.ImportApplicationType, "endorsements"),
]
