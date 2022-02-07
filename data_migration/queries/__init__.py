from typing import NamedTuple

from django.db.models import Model

from data_migration import models as dm_models
from web import models as web_models

from . import reference as ref_queries

QueryModel = NamedTuple("QueryModel", [("query", str), ("model", Model)])
SourceTarget = NamedTuple("SourceTarget", [("source", Model), ("target", Model)])
M2M = NamedTuple("M2M", [("source", Model), ("target", Model), ("field", str)])

ref_query_model = [
    QueryModel(ref_queries.country, dm_models.Country),
    QueryModel(ref_queries.country_group, dm_models.CountryGroup),
    QueryModel(ref_queries.country_group_country, dm_models.CountryGroupCountry),
    QueryModel(ref_queries.country_translation_set, dm_models.CountryTranslationSet),
    QueryModel(ref_queries.country_translation, dm_models.CountryTranslation),
    QueryModel(ref_queries.unit, dm_models.Unit),
    QueryModel(ref_queries.commodity_type, dm_models.CommodityType),
    QueryModel(ref_queries.commodity_group, dm_models.CommodityGroup),
    QueryModel(ref_queries.commodity, dm_models.Commodity),
    QueryModel(ref_queries.commodity_group_commodity, dm_models.CommodityGroupCommodity),
]

ref_source_target = [
    SourceTarget(getattr(dm_models, model_name), getattr(web_models, model_name))
    for model_name in [
        "Country",
        "CountryGroup",
        "CountryTranslationSet",
        "CountryTranslation",
        "Unit",
        "CommodityType",
        "CommodityGroup",
        "Commodity",
    ]
]

ref_m2m = [
    M2M(dm_models.CountryGroupCountry, web_models.CountryGroup, "countries"),
    M2M(dm_models.CommodityGroupCommodity, web_models.CommodityGroup, "commodities"),
]
