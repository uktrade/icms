from typing import Union

from . import forms, models

GoodsModel = Union[
    models.SILGoodsSection1,
    models.SILGoodsSection2,
    models.SILGoodsSection5,
    models.SILGoodsSection582Obsolete,  # /PS-IGNORE
    models.SILGoodsSection582Other,  # /PS-IGNORE
    models.SILLegacyGoods,
]
GoodsModelT = type[GoodsModel]

GoodsForm = Union[
    forms.SILGoodsSection1Form,
    forms.SILGoodsSection2Form,
    forms.SILGoodsSection5Form,
    forms.SILGoodsSection582ObsoleteForm,  # /PS-IGNORE
    forms.SILGoodsSection582OtherForm,  # /PS-IGNORE
]
GoodsFormT = type[GoodsForm]

ResponsePrepGoodsForm = Union[
    forms.ResponsePrepSILGoodsSection1Form,
    forms.ResponsePrepSILGoodsSection2Form,
    forms.ResponsePrepSILGoodsSection5Form,
    forms.ResponsePrepSILGoodsSection582ObsoleteForm,  # /PS-IGNORE
    forms.ResponsePrepSILGoodsSection582OtherForm,  # /PS-IGNORE
]

ResponsePrepGoodsFormT = type[ResponsePrepGoodsForm]

SILReportFirearmModel = Union[
    models.SILSupplementaryReportFirearmSection1,
    models.SILSupplementaryReportFirearmSection2,
    models.SILSupplementaryReportFirearmSection5,
    models.SILSupplementaryReportFirearmSection582Obsolete,  # /PS-IGNORE
    models.SILSupplementaryReportFirearmSection582Other,  # /PS-IGNORE
    models.SILSupplementaryReportFirearmSectionLegacy,
]

SILReportFirearmModelT = type[SILReportFirearmModel]

SILReportFirearmFormT = type[
    Union[
        forms.SILSupplementaryReportFirearmSection1Form,
        forms.SILSupplementaryReportFirearmSection2Form,
        forms.SILSupplementaryReportFirearmSection5Form,
        forms.SILSupplementaryReportFirearmSection582ObsoleteForm,  # /PS-IGNORE
        forms.SILSupplementaryReportFirearmSection582OtherForm,  # /PS-IGNORE
        forms.SILSupplementaryReportFirearmSectionLegacyForm,
    ]
]
