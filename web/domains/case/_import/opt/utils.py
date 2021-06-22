from typing import Type

from .forms import (
    FurtherQuestionsBaseOPTForm,
    FurtherQuestionsEmploymentDecreasedOPTForm,
    FurtherQuestionsFurtherAuthorisationOPTForm,
    FurtherQuestionsNewApplicationOPTForm,
    FurtherQuestionsPastBeneficiaryOPTForm,
    FurtherQuestionsPriorAuthorisationOPTForm,
    FurtherQuestionsSubcontractProductionOPTForm,
)
from .models import OutwardProcessingTradeFile


def get_fq_form(file_type: str) -> Type[FurtherQuestionsBaseOPTForm]:
    """Get the edit form for a specific Further Questions type."""

    form_class_map = {
        OutwardProcessingTradeFile.Type.FQ_EMPLOYMENT_DECREASED: FurtherQuestionsEmploymentDecreasedOPTForm,
        OutwardProcessingTradeFile.Type.FQ_PRIOR_AUTHORISATION: FurtherQuestionsPriorAuthorisationOPTForm,
        OutwardProcessingTradeFile.Type.FQ_PAST_BENEFICIARY: FurtherQuestionsPastBeneficiaryOPTForm,
        OutwardProcessingTradeFile.Type.FQ_NEW_APPLICATION: FurtherQuestionsNewApplicationOPTForm,
        OutwardProcessingTradeFile.Type.FQ_FURTHER_AUTHORISATION: FurtherQuestionsFurtherAuthorisationOPTForm,
        OutwardProcessingTradeFile.Type.FQ_SUBCONTRACT_PRODUCTION: FurtherQuestionsSubcontractProductionOPTForm,
    }

    return form_class_map[file_type]  # type: ignore[index]


def get_fq_page_name(file_type: str) -> str:
    """Get a human-readable page name for a specific Further Questions type."""

    form_class_map = {
        OutwardProcessingTradeFile.Type.FQ_EMPLOYMENT_DECREASED: "Level of employment",
        OutwardProcessingTradeFile.Type.FQ_PRIOR_AUTHORISATION: "Prior Authorisation",
        OutwardProcessingTradeFile.Type.FQ_PAST_BENEFICIARY: "Past Beneficiary",
        OutwardProcessingTradeFile.Type.FQ_NEW_APPLICATION: "New Application",
        OutwardProcessingTradeFile.Type.FQ_FURTHER_AUTHORISATION: "Further Authorisation",
        OutwardProcessingTradeFile.Type.FQ_SUBCONTRACT_PRODUCTION: "Subcontract production",
    }

    return form_class_map[file_type]  # type: ignore[index]
