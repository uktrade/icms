#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View

from web.auth.mixins import RequireRegisteredMixin
from web.domains.template.models import Template
from web.notify import notify
from web.views import ModelDetailView, ModelFilterView, ModelUpdateView
from web.views.mixins import PostActionMixin

from .actions import Edit, Retract
from .actions import View as Display
from .forms import (
    MailshotFilter,
    MailshotForm,
    MailshotReadonlyForm,
    MailshotRetractForm,
    ReceivedMailshotsFilter,
)
from .models import Mailshot


class ReceivedMailshotsView(ModelFilterView):
    template_name = "web/domains/mailshot/received.html"
    model = Mailshot
    filterset_class = ReceivedMailshotsFilter
    page_title = "Received Mailshots"

    def has_permission(self):
        user = self.request.user
        return user.is_superuser or user.is_importer() or user.is_exporter()

    def get_filterset(self):
        return super().get_filterset(user=self.request.user)

    class Display:
        fields = ["id", "published", "title", "description"]
        fields_config = {
            "id": {"header": "Reference"},
            "published": {"header": "Published"},
            "title": {"header": "Title"},
            "description": {"header": "Description"},
        }
        actions = [Display()]


class MailshotListView(ModelFilterView):
    template_name = "web/domains/mailshot/list.html"
    model = Mailshot
    filterset_class = MailshotFilter
    permission_required = "web.mailshot_access"
    page_title = "Maintain Mailshots"

    class Display:
        fields = [
            "id",
            "status_verbose",
            ("retracted", "published", "started"),
            "title",
            "description",
        ]
        fields_config = {
            "id": {"header": "Reference"},
            "started": {"header": "Activity", "label": "<strong>Started</strong>"},
            "published": {"no_header": True, "label": "<strong>Published</strong>"},
            "retracted": {"no_header": True, "label": "<strong>Retracted</strong>"},
            "title": {"header": "Title"},
            "status_verbose": {"header": "Status"},
            "description": {"header": "Description"},
        }
        actions = [Edit(), Display(), Retract()]


class MailshotCreateView(RequireRegisteredMixin, View):
    MAILSHOT_TEMPLATE_CODE = "PUBLISH_MAILSHOT"
    permission_required = "web.mailshot_access"

    def get(self, request):
        """
        Create a draft mailshot and redirect to edit
        """
        template = Template.objects.get(template_code=self.MAILSHOT_TEMPLATE_CODE)
        mailshot = Mailshot()
        mailshot.email_subject = template.template_title
        mailshot.email_body = template.template_content
        mailshot.created_by = request.user
        mailshot.save()
        return redirect(reverse_lazy("mailshot-edit", args=(mailshot.id,)))


class MailshotEditView(PostActionMixin, ModelUpdateView):
    template_name = "web/domains/mailshot/edit.html"
    form_class = MailshotForm
    model = Mailshot
    success_url = reverse_lazy("mailshot-list")
    cancel_url = success_url
    permission_required = "web.mailshot_access"

    def handle_notification(self, mailshot):
        if mailshot.is_email:
            notify.mailshot(mailshot)

    def form_valid(self, form):
        """
        Publish mailshot if form is valid.
        """
        mailshot = form.instance
        mailshot.status = Mailshot.PUBLISHED
        mailshot.published_datetime = timezone.now()
        mailshot.published_by = self.request.user
        response = super().form_valid(form)
        if response.status_code == 302 and response.url == self.success_url:
            self.handle_notification(mailshot)
        return response

    def save_draft(self, request, pk):
        """
        Saves mailshot draft bypassing all validation.
        """
        self.object = super().get_object()
        form = self.get_form()
        for field in form:
            field.field.required = False
        if form.is_valid():
            return super().form_valid(form)
        else:
            return super().form_invalid(form)

    def cancel(self, request, pk):
        mailshot = Mailshot.objects.get(pk=pk)
        mailshot.status = Mailshot.CANCELLED
        mailshot.save()
        messages.success(request, "Mailshot cancelled successfully")
        return redirect(self.success_url)

    def get_success_message(self, cleaned_data):
        action = self.request.POST.get("action")
        if action and action == "save_draft":
            return super().get_success_message(cleaned_data)

        return f"{self.object} published successfully"

    def get_queryset(self):
        """
        Only allow DRAFT mailshots to be edited by filtering.
        Leads to 404 otherwise
        """
        return Mailshot.objects.filter(status=Mailshot.DRAFT)


class MailshotDetailView(ModelDetailView):
    template_name = "model/view.html"
    form_class = MailshotForm
    model = Mailshot
    cancel_url = reverse_lazy("mailshot-list")
    permission_required = "web.mailshot_access"

    def has_permission(self):
        user = self.request.user
        has_permission = super().has_permission()
        if has_permission:
            return True

        mailshot = self.get_object()
        if mailshot.is_to_importers and user.is_importer():
            return True
        if mailshot.is_to_exporters and user.is_exporter():
            return True

        return False


class MailshotRetractView(ModelUpdateView):
    RETRACT_TEMPLATE_CODE = "RETRACT_MAILSHOT"
    template_name = "web/domains/mailshot/retract.html"
    form_class = MailshotRetractForm
    model = Mailshot
    success_url = reverse_lazy("mailshot-list")
    cancel_url = success_url
    permission_required = "web.mailshot_access"

    def __init__(self, *args, **kwargs):
        template = Template.objects.get(template_code=self.RETRACT_TEMPLATE_CODE)
        self.initial = {
            "retract_email_subject": template.template_title,
            "retract_email_body": template.template_content,
        }

    def get_form(self, *args, **kwargs):
        """
        Add mailshot form into the context for displaying mailshot details
        """
        form = super().get_form(*args, **kwargs)
        self.view_form = MailshotReadonlyForm(instance=self.object)
        return form

    def handle_notification(self, mailshot):
        if mailshot.is_retraction_email:
            notify.retract_mailshot(mailshot)

    def form_valid(self, form):
        """
        Retract mailshot if form is valid.
        """
        mailshot = form.instance
        mailshot.status = Mailshot.RETRACTED
        mailshot.retracted_datetime = timezone.now()
        mailshot.retracted_by = self.request.user
        response = super().form_valid(form)
        if response.status_code == 302 and response.url == self.success_url:
            self.handle_notification(mailshot)
        return response

    def get_success_message(self, cleaned_data):
        return f"{self.object} retracted successfully"

    def get_queryset(self):
        """
        Only allow PUBLISHED mailshots to be retracted by filtering.
        Leads to 404 otherwise
        """
        return Mailshot.objects.filter(status=Mailshot.PUBLISHED)

    def get_page_title(self):
        return f"Retract {self.object}"
