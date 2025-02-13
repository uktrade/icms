from http import HTTPStatus

from django.urls import reverse
from pytest_django.asserts import assertContains

from web.models import UserFeedbackSurvey
from web.tests.auth.auth import AuthTestCase


class TestFeedbackSurvey(AuthTestCase):
    def test_survey_success(self, exporter_client, cfs_app_submitted):
        app = cfs_app_submitted
        url = reverse("survey:provide_application_feedback", kwargs={"process_pk": app.pk})
        data = {
            "satisfaction": "VERY_DISSATISFIED",
            "issues": ["UNABLE_TO_LOAD"],
            "find_service": "VERY_EASY",
            "additional_support": "NO",
            "service_improvements": "Nothing",
            "future_contact": "yes",
        }
        response = exporter_client.post(url, data=data, follow=True)
        assertContains(response, "Survey submitted. Thank you for your feedback.")

        survey = UserFeedbackSurvey.objects.get(process_id=app.pk)
        assert survey.satisfaction == "VERY_DISSATISFIED"
        assert survey.issues == ["UNABLE_TO_LOAD"]
        assert survey.find_service == "VERY_EASY"
        assert survey.additional_support == "NO"
        assert survey.service_improvements == "Nothing"
        assert survey.future_contact == "yes"
        assert survey.site == "export-a-certificate"

    def test_survey_other_options_required(self, importer_client, fa_sil_app_submitted):
        app = fa_sil_app_submitted
        url = reverse("survey:provide_application_feedback", kwargs={"process_pk": app.pk})
        data = {
            "satisfaction": "SATISFIED",
            "issues": ["UNABLE_TO_LOAD", "OTHER"],
            "find_service": "DIFFICULT",
            "additional_support": "EMAIL",
            "service_improvements": "Something",
            "future_contact": "no",
        }
        response = importer_client.post(url, data=data)

        form = response.context["form"]
        assert not form.is_valid()
        assert (
            form.errors.as_data()["issue_details"][0].message
            == "Enter details of the issue you had."
        )

        data["issues"] = []
        response = importer_client.post(url, data=data)
        form = response.context["form"]
        assert form.errors.as_data()["issues"][0].message == "Select at least one issue."

        assertContains(response, "Select at least one issue.", status_code=HTTPStatus.OK)

    def test_survey_submitted_once(self, exporter_client, cfs_app_submitted):
        app = cfs_app_submitted
        url = reverse("survey:provide_application_feedback", kwargs={"process_pk": app.pk})
        data = {
            "satisfaction": "VERY_SATISFIED",
            "issues": ["UNABLE_TO_LOAD", "OTHER"],
            "issue_details": "Test",
            "find_service": "VERY_DIFFICULT",
            "find_service_details": "Test",
            "additional_support": "NO",
            "service_improvements": "Nothing",
            "future_contact": "yes",
        }
        response = exporter_client.post(url, data=data, follow=True)
        assertContains(response, "Survey submitted. Thank you for your feedback.")

        response = exporter_client.get(url, follow=True)
        assertContains(response, "This survey has already been submitted.")

    def test_survey_access(self, exporter_client, fa_sil_app_submitted):
        sil_url = reverse(
            "survey:provide_application_feedback", kwargs={"process_pk": fa_sil_app_submitted.pk}
        )

        response = exporter_client.get(sil_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = exporter_client.get("survey/0/")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_generic_entry(self, exporter_client):
        assert UserFeedbackSurvey.objects.count() == 0
        url = reverse("survey:provide_generic_feedback")
        data = {
            "satisfaction": "VERY_SATISFIED",
            "issues": ["UNABLE_TO_LOAD", "OTHER"],
            "issue_details": "Test",
            "find_service": "VERY_DIFFICULT",
            "find_service_details": "Test",
            "additional_support": "NO",
            "service_improvements": "Nothing",
            "future_contact": "yes",
        }
        exporter_client.post(url, data=data)
        assert UserFeedbackSurvey.objects.count() == 1
        new_survey = UserFeedbackSurvey.objects.first()
        assert new_survey.satisfaction == "VERY_SATISFIED"
        assert new_survey.issues == ["UNABLE_TO_LOAD", "OTHER"]
        assert new_survey.issue_details == "Test"
        assert new_survey.find_service == "VERY_DIFFICULT"
        assert new_survey.find_service_details == "Test"
        assert new_survey.additional_support == "NO"
        assert new_survey.service_improvements == "Nothing"
        assert new_survey.future_contact == "yes"
        assert new_survey.site == "export-a-certificate"
        assert not new_survey.referrer_path

    def test_generic_entry_referrer_path(self, exporter_client):
        url = reverse("survey:provide_generic_feedback") + "?referrer_path=/test/test2/test3"
        data = {
            "satisfaction": "VERY_SATISFIED",
            "issues": ["UNABLE_TO_LOAD", "OTHER"],
            "issue_details": "Test",
            "find_service": "VERY_DIFFICULT",
            "find_service_details": "Test",
            "additional_support": "NO",
            "service_improvements": "Nothing",
            "future_contact": "yes",
        }
        exporter_client.post(url, data=data)
        new_survey = UserFeedbackSurvey.objects.first()
        assert new_survey.referrer_path == "/test/test2/test3"

    def test_footer_feedback_link(self, exporter_client, cfs_app_submitted):
        response = exporter_client.get(reverse("workbasket"))
        assertContains(response, "Provide feedback", count=1)
        assertContains(
            response,
            reverse("survey:provide_generic_feedback") + "?referrer_path=/workbasket/",
            count=1,
        )

        view_case_url = reverse(
            "case:view", kwargs={"application_pk": cfs_app_submitted.pk, "case_type": "export"}
        )
        response = exporter_client.get(view_case_url)
        assertContains(response, "Provide feedback", count=1)
        assertContains(
            response,
            reverse("survey:provide_generic_feedback") + f"?referrer_path={view_case_url}",
            count=1,
        )
