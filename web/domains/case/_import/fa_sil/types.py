from typing import Type, Union

from . import forms, models

GoodsModel = Union[
    models.SILGoodsSection1,
    models.SILGoodsSection2,
    models.SILGoodsSection5,
    models.SILGoodsSection582Obsolete,
    models.SILGoodsSection582Other,
]
GoodsModelT = Type[GoodsModel]

GoodsForm = Union[
    forms.SILGoodsSection1Form,
    forms.SILGoodsSection2Form,
    forms.SILGoodsSection5Form,
    forms.SILGoodsSection582ObsoleteForm,
    forms.SILGoodsSection582OtherForm,
]
GoodsFormT = Type[GoodsForm]

ResponsePrepGoodsForm = Union[
    forms.ResponsePrepSILGoodsSection1Form,
    forms.ResponsePrepSILGoodsSection2Form,
    forms.ResponsePrepSILGoodsSection5Form,
    forms.ResponsePrepSILGoodsSection582ObsoleteForm,
    forms.ResponsePrepSILGoodsSection582OtherForm,
]

ResponsePrepGoodsFormT = Type[ResponsePrepGoodsForm]

SILReportFirearmModels = Union[
    models.SILSupplementaryReportFirearmSection1,
    models.SILSupplementaryReportFirearmSection2,
    models.SILSupplementaryReportFirearmSection5,
    models.SILSupplementaryReportFirearmSection582Obsolete,
    models.SILSupplementaryReportFirearmSection582Other,
]

SILReportFirearmFormsT = Type[
    Union[
        forms.SILSupplementaryReportFirearmSection1Form,
        forms.SILSupplementaryReportFirearmSection2Form,
        forms.SILSupplementaryReportFirearmSection5Form,
        forms.SILSupplementaryReportFirearmSection582ObsoleteForm,
        forms.SILSupplementaryReportFirearmSection582OtherForm,
    ]
]
