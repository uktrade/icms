from typing import Literal, NamedTuple

from django.db.models import Model

from data_migration import models as dm_models
from data_migration.models import task
from web import models as web_models

from . import import_application, reference

QueryModel = NamedTuple("QueryModel", [("query", str), ("model", Model)])
SourceTarget = NamedTuple("SourceTarget", [("source", Model), ("target", Model)])
M2M = NamedTuple("M2M", [("source", Model), ("target", Model), ("field", str)])


def source_target_list(lst: list[str]):
    return [
        SourceTarget(getattr(dm_models, model_name), getattr(web_models, model_name))
        for model_name in lst
    ]


user_source_target = source_target_list(["User", "Importer", "Office"])

ref_query_model = [
    QueryModel(reference.country, dm_models.Country),
    QueryModel(reference.country_group, dm_models.CountryGroup),
    QueryModel(reference.country_group_country, dm_models.CountryGroupCountry),
    QueryModel(reference.country_translation_set, dm_models.CountryTranslationSet),
    QueryModel(reference.country_translation, dm_models.CountryTranslation),
    QueryModel(reference.unit, dm_models.Unit),
    QueryModel(reference.commodity_type, dm_models.CommodityType),
    QueryModel(reference.commodity_group, dm_models.CommodityGroup),
    QueryModel(reference.commodity, dm_models.Commodity),
    QueryModel(reference.commodity_group_commodity, dm_models.CommodityGroupCommodity),
    QueryModel(import_application.import_application_type, dm_models.ImportApplicationType),
    QueryModel(import_application.usage, dm_models.Usage),
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
        "ImportApplicationType",
        "Usage",
    ]
)

ref_m2m = [
    M2M(dm_models.CountryGroupCountry, web_models.CountryGroup, "countries"),
    M2M(dm_models.CommodityGroupCommodity, web_models.CommodityGroup, "commodities"),
]

ia_query_model = [
    QueryModel(import_application.wood_application, dm_models.WoodQuotaApplication),
    QueryModel(import_application.wood_checklist, dm_models.WoodQuotaChecklist),
    QueryModel(import_application.textiles_application, dm_models.TextilesApplication),
    QueryModel(import_application.textiles_checklist, dm_models.TextilesChecklist),
]

# Possibly refactor to import process and import application by process type
ia_source_target = source_target_list(
    [
        "Process",
        "ImportApplication",
        "WoodQuotaApplication",
        "WoodQuotaChecklist",
        "TextilesApplication",
        "TextilesChecklist",
    ]
)

DATA_TYPE = Literal["reference", "import_application", "user"]

DATA_TYPE_QUERY_MODEL: dict[str, list[QueryModel]] = {
    "reference": ref_query_model,
    "import_application": ia_query_model,
}

DATA_TYPE_SOURCE_TARGET: dict[str, list[SourceTarget]] = {
    "user": user_source_target,
    "reference": ref_source_target,
    "import_application": ia_source_target,
}

DATA_TYPE_M2M: dict[str, list[M2M]] = {
    "user": [],
    "reference": ref_m2m,
    "import_application": [],
}

TASK_LIST = [
    task.PrepareTask,
    task.ProcessTask,
]
