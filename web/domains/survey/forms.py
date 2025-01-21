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
        widgets = {"issues": CheckboxSelectMultiple(choices=UserFeedbackSurvey.IssuesChoices)}

    def clean(self) -> dict[str, Any]:
        data = super().clean()

        if data.get("find_service") in (
            UserFeedbackSurvey.EaseFindChoices.DIFFICULT,
            UserFeedbackSurvey.EaseFindChoices.VERY_DIFFICULT,
        ) and not data.get("find_service_details"):
            self.add_error("find_service_details", "Enter why the service was difficult to find.")

        if UserFeedbackSurvey.IssuesChoices.OTHER in data.get("issues", []) and not data.get(
            "issue_details"
        ):
            self.add_error("issue_details", "Enter details of the issue you had.")
        return data
