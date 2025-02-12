from typing import Any

from django import forms

from web.forms.widgets import CheckboxSelectMultiple

from .models import UserFeedbackSurvey


class UserFeedbackForm(forms.ModelForm):
    class Meta:
        fields = (
            "satisfaction",
            "issues",
            "issue_details",
            "find_service",
            "find_service_details",
            "additional_support",
            "service_improvements",
            "future_contact",
        )
        model = UserFeedbackSurvey
        widgets = {
            "issues": CheckboxSelectMultiple(choices=UserFeedbackSurvey.IssuesChoices),
        }

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if cleaned_data["satisfaction"] != UserFeedbackSurvey.SatisfactionLevel.VERY_SATISFIED:
            if not cleaned_data.get("issues"):
                self.add_error("issues", "Select at least one issue.")

        if UserFeedbackSurvey.IssuesChoices.OTHER in cleaned_data.get(
            "issues", []
        ) and not cleaned_data.get("issue_details"):
            self.add_error("issue_details", "Enter details of the issue you had.")

        return cleaned_data
