from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from web.domains.case.types import ImpOrExp
from web.domains.user.models import User
from web.flow.models import Process
from web.models import UserFeedbackSurvey
from web.permissions import AppChecker, Perms

from .forms import UserFeedbackForm


def check_user_submitted_and_can_edit_application(user: User, application: ImpOrExp) -> bool:
    """Check if the user has submitted the application and can edit it."""
    return application.submitted_by == user and AppChecker(user, application).can_edit()


class DoYouWantToProvideFeedbackView(LoginRequiredMixin, TemplateView):
    template_name = "web/domains/survey/do-you-want-to-provide-feedback.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        process = Process.objects.get(pk=self.kwargs["process_pk"])
        context["reference"] = process.get_specific_model().get_reference()
        return context

    def has_permission(self):
        application = Process.objects.get(pk=self.kwargs["process_pk"]).get_specific_model()
        return check_user_submitted_and_can_edit_application(self.request.user, application)


class ProvideFeedbackView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = "web/domains/survey/user-feedback-survey.html"
    form_class = UserFeedbackForm
    success_url = reverse_lazy("workbasket")
    page_title = "Survey"

    def has_permission(self):
        return self.request.user.has_perm(Perms.sys.importer_access) or self.request.user.has_perm(
            Perms.sys.exporter_access
        )

    def populate_feedback_survey(self, obj: UserFeedbackSurvey) -> UserFeedbackSurvey:
        obj.created_by = self.request.user
        obj.site = self.request.site
        obj.referrer_path = self.request.GET.get("referrer_path", "")

        return obj

    def form_valid(self, form: UserFeedbackForm) -> HttpResponse:
        """If the form is valid, save the associated model."""
        obj: UserFeedbackSurvey = form.save(commit=False)
        obj = self.populate_feedback_survey(obj)
        obj.save()
        messages.success(self.request, "Survey submitted. Thank you for your feedback.")
        return super().form_valid(form)


class ProvideApplicationFeedbackView(ProvideFeedbackView):
    def populate_feedback_survey(self, obj: UserFeedbackSurvey) -> UserFeedbackSurvey:
        obj = super().populate_feedback_survey(obj)
        obj.process = self.process

        return obj

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.process = Process.objects.get(pk=self.kwargs["process_pk"])
        try:
            UserFeedbackSurvey.objects.get(process=self.process)
            messages.success(request, "This survey has already been submitted.")
            return redirect(self.success_url)
        except UserFeedbackSurvey.DoesNotExist:
            return super().dispatch(request, *args, **kwargs)

    def has_permission(self) -> bool:
        application = self.process.get_specific_model()
        return super().has_permission() and check_user_submitted_and_can_edit_application(
            self.request.user, application
        )
