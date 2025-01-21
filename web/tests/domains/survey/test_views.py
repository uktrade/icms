from http import HTTPStatus

from django.urls import reverse
from pytest_django.asserts import assertContains

from web.models import UserFeedbackSurvey
from web.tests.auth.auth import AuthTestCase


class TestFeedbackSurvery(AuthTestCase):
    def test_survey_success(self, exporter_client, cfs_app_submitted):
        app = cfs_app_submitted
        url = reverse("survey:user-feedback", kwargs={"process_pk": app.pk})
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
        url = reverse("survey:user-feedback", kwargs={"process_pk": app.pk})
        data = {
            "satisfaction": "VERY_SATISFIED",
            "issues": ["UNABLE_TO_LOAD", "OTHER"],
            "find_service": "DIFFICULT",
            "additional_support": "EMAIL",
            "service_improvements": "Something",
            "future_contact": "no",
        }
        response = importer_client.post(url, data=data)

        assertContains(
            response, "Enter why the service was difficult to find.", status_code=HTTPStatus.OK
        )
        assertContains(response, "Enter details of the issue you had.", status_code=HTTPStatus.OK)

    def test_survey_submitted_once(self, exporter_client, cfs_app_submitted):
        app = cfs_app_submitted
        url = reverse("survey:user-feedback", kwargs={"process_pk": app.pk})
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
        sil_url = reverse("survey:user-feedback", kwargs={"process_pk": fa_sil_app_submitted.pk})

        response = exporter_client.get(sil_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = exporter_client.get("survey/0/")
        assert response.status_code == HTTPStatus.NOT_FOUND
