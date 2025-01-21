from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from web.flow.models import Process
from web.models import UserFeedbackSurvey
from web.permissions import AppChecker

from .forms import UserFeedbackForm


class UserFeedbackView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = "web/domains/survey/user-feedback-survey.html"
    form_class = UserFeedbackForm
    success_url = reverse_lazy("workbasket")
    page_title = "Survey"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.process = Process.objects.get(pk=self.kwargs["process_pk"])
        try:
            UserFeedbackSurvey.objects.get(process=self.process)
            messages.success(request, "This survey has already been submitted.")
            return redirect(self.success_url)
        except UserFeedbackSurvey.DoesNotExist:
            return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: UserFeedbackForm) -> bool:
        """If the form is valid, save the associated model."""
        obj: UserFeedbackSurvey = form.save(commit=False)
        obj.created_by = self.request.user
        obj.process = self.process
        obj.site = self.request.site
        self.object = obj.save()
        messages.success(self.request, "Survey submitted. Thank you for your feedback.")
        return super().form_valid(form)

    def has_permission(self) -> bool:
        application = Process.objects.get(pk=self.kwargs["process_pk"]).get_specific_model()
        submitted_by_user = application.submitted_by == self.request.user
        can_edit = AppChecker(self.request.user, application).can_edit()

        return submitted_by_user and can_edit
