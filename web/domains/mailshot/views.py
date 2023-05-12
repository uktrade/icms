from typing import TYPE_CHECKING, Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_GET, require_POST
from django.views.generic.detail import DetailView

from web.auth.mixins import RequireRegisteredMixin
from web.domains.case.forms import DocumentForm
from web.domains.case.services import reference
from web.domains.file.utils import create_file_model
from web.models import Template, User
from web.notify import notify
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import get_file_from_s3
from web.views import ModelFilterView, ModelUpdateView
from web.views.mixins import PostActionMixin

from .actions import Edit, Republish, Retract
from .actions import View as Display
from .actions import ViewReceived
from .forms import (
    MailshotFilter,
    MailshotForm,
    MailshotRetractForm,
    ReceivedMailshotsFilter,
)
from .models import Mailshot

if TYPE_CHECKING:
    from django.db import QuerySet


class ReceivedMailshotsView(ModelFilterView):
    template_name = "web/domains/mailshot/received.html"
    model = Mailshot
    filterset_class = ReceivedMailshotsFilter
    page_title = "Received Mailshots"

    def has_permission(self) -> bool:
        return _check_permission(self.request.user)

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
        actions = [ViewReceived()]


class MailshotListView(ModelFilterView):
    template_name = "web/domains/mailshot/list.html"
    model = Mailshot
    filterset_class = MailshotFilter
    permission_required = Perms.sys.ilb_admin
    page_title = "Maintain Mailshots"

    class Display:
        fields = [
            "reference",
            "status_verbose",
            ("retracted", "published", "started"),
            "title",
            "description",
        ]
        fields_config = {
            "reference": {"header": "Reference", "method": "get_reference"},
            "started": {"header": "Activity", "label": "<strong>Started</strong>"},
            "published": {"no_header": True, "label": "<strong>Published</strong>"},
            "retracted": {"no_header": True, "label": "<strong>Retracted</strong>"},
            "title": {"header": "Title"},
            "status_verbose": {"header": "Status"},
            "description": {"header": "Description"},
        }

        actions = [Edit(), Display(), Retract(), Republish()]

    def get_queryset(self) -> "QuerySet[Mailshot]":
        qs = super().get_queryset()

        max_version = Mailshot.objects.filter(reference=models.OuterRef("reference")).order_by(
            "-version"
        )

        mailshots = qs.annotate(
            last_version_for_ref=models.Subquery(max_version.values("version")[:1])
        )

        return mailshots.order_by("-pk")


class MailshotCreateView(RequireRegisteredMixin, View):
    MAILSHOT_TEMPLATE_CODE = "PUBLISH_MAILSHOT"
    permission_required = Perms.sys.ilb_admin

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
    permission_required = Perms.sys.ilb_admin
    pk_url_kwarg = "mailshot_pk"

    def get_success_url(self):
        action = self.request.POST.get("action")

        if action and action == "save_draft":
            return reverse("mailshot-edit", kwargs={"mailshot_pk": self.object.pk})

        return reverse("mailshot-list")

    def handle_notification(self, mailshot):
        if mailshot.is_email:
            notify.mailshot(mailshot)

    def form_valid(self, form):
        """
        Publish mailshot if form is valid.
        """

        with transaction.atomic():
            mailshot = form.save(commit=False)
            mailshot.status = Mailshot.Statuses.PUBLISHED
            mailshot.published_datetime = timezone.now()
            mailshot.published_by = self.request.user

            if not mailshot.reference:
                mailshot.reference = reference.get_mailshot_reference(
                    self.request.icms.lock_manager
                )
                mailshot.version = models.F("version") + 1

            mailshot.save()

        mailshot.refresh_from_db()
        self.object = mailshot

        self.handle_notification(mailshot)

        # Finally add the success message before returning the response.
        messages.success(self.request, self.get_success_message(form.cleaned_data))

        return HttpResponseRedirect(self.get_success_url())

    def publish(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        """Publish mailshot post action."""
        self.object = self.get_object()
        form = self.get_form()

        has_documents = self.object.documents.filter(is_active=True).exists()

        if not has_documents:
            form.add_error(None, "A document must be uploaded before publishing")

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def save_draft(self, request, **kwargs):
        """Saves mailshot draft post action bypassing all validation."""

        self.object = self.get_object()
        form = self.get_form()
        for field in form:
            field.field.required = False
        if form.is_valid():
            return super().form_valid(form)
        else:
            return super().form_invalid(form)

    def cancel(self, request, **kwargs):
        """Cancel post action"""

        mailshot = self.get_object()
        mailshot.status = Mailshot.Statuses.CANCELLED
        mailshot.save()
        messages.success(request, "Mailshot cancelled successfully")
        return redirect(self.success_url)

    def get_success_message(self, cleaned_data):
        # TODO: ICMSLST-1173 fix success message
        action = self.request.POST.get("action")
        if action and action == "save_draft":
            return super().get_success_message(cleaned_data)

        return f"{self.object.get_reference()} published successfully"

    def get_queryset(self):
        """
        Only allow DRAFT mailshots to be edited by filtering.
        Leads to 404 otherwise
        """
        return Mailshot.objects.filter(status=Mailshot.Statuses.DRAFT)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documents"] = self.object.documents.filter(is_active=True)

        return context


class MailshotDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    template_name = "web/domains/mailshot/view.html"
    model = Mailshot
    pk_url_kwarg = "mailshot_pk"
    permission_required = Perms.sys.ilb_admin

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["documents"] = self.object.documents.filter(is_active=True)
        context["page_title"] = f"Viewing Mailshot ({self.object.get_reference()})"

        return context


class MailshotReceivedDetailView(MailshotDetailView):
    template_name = "web/domains/mailshot/view_received.html"

    def has_permission(self) -> bool:
        user: User = self.request.user

        if user.has_perm(Perms.sys.ilb_admin):
            return True

        mailshot: Mailshot = self.get_object()

        if mailshot.is_to_importers and user.has_perm("web.importer_access"):
            return True

        if mailshot.is_to_exporters and user.has_perm("web.export_access"):
            return True

        return False


class MailshotRetractView(ModelUpdateView):
    RETRACT_TEMPLATE_CODE = "RETRACT_MAILSHOT"
    template_name = "web/domains/mailshot/retract.html"
    form_class = MailshotRetractForm
    model = Mailshot
    success_url = reverse_lazy("mailshot-list")
    cancel_url = success_url
    permission_required = Perms.sys.ilb_admin
    pk_url_kwarg = "mailshot_pk"

    def __init__(self, *args, **kwargs):
        template = Template.objects.get(template_code=self.RETRACT_TEMPLATE_CODE)
        self.initial = {
            "retract_email_subject": template.template_title,
            "retract_email_body": template.template_content,
        }

    def handle_notification(self, mailshot):
        if mailshot.is_retraction_email:
            notify.retract_mailshot(mailshot)

    def form_valid(self, form):
        """
        Retract mailshot if form is valid.
        """
        mailshot = form.instance
        mailshot.status = Mailshot.Statuses.RETRACTED
        mailshot.retracted_datetime = timezone.now()
        mailshot.retracted_by = self.request.user
        response = super().form_valid(form)

        if response.status_code == 302 and response.url == self.success_url:
            self.handle_notification(mailshot)

        return response

    def get_success_message(self, cleaned_data):
        return f"{self.object.get_reference()} retracted successfully"

    def get_queryset(self):
        """
        Only allow PUBLISHED mailshots to be retracted by filtering.
        Leads to 404 otherwise
        """
        return Mailshot.objects.filter(status=Mailshot.Statuses.PUBLISHED)

    def get_page_title(self):
        return f"Retract {self.object.get_reference()}"


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def add_document(request: AuthenticatedHttpRequest, *, mailshot_pk: int) -> HttpResponse:
    with transaction.atomic():
        mailshot = get_object_or_404(Mailshot.objects.select_for_update(), pk=mailshot_pk)

        if request.method == "POST":
            form = DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")
                create_file_model(document, request.user, mailshot.documents)

                return redirect(reverse("mailshot-edit", kwargs={"mailshot_pk": mailshot_pk}))
        else:
            form = DocumentForm()

        context = {
            "mailshot": mailshot,
            "form": form,
            "page_title": "Mailshot - Add document",
        }

        return render(request, "web/domains/mailshot/add_document.html", context)


@require_GET
@login_required
def view_document(
    request: AuthenticatedHttpRequest, *, mailshot_pk: int, document_pk: int
) -> HttpResponse:
    mailshot = get_object_or_404(Mailshot, pk=mailshot_pk)
    document = get_object_or_404(mailshot.documents, pk=document_pk)

    has_perm = _check_permission(request.user)
    if not has_perm:
        raise PermissionDenied

    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


@require_POST
@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def delete_document(
    request: AuthenticatedHttpRequest, *, mailshot_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        mailshot = get_object_or_404(Mailshot.objects.select_for_update(), pk=mailshot_pk)

        document = mailshot.documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("mailshot-edit", kwargs={"mailshot_pk": mailshot_pk}))


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def republish(request: AuthenticatedHttpRequest, *, mailshot_pk: int) -> HttpResponse:
    with transaction.atomic():
        mailshot = get_object_or_404(Mailshot.objects.select_for_update(), pk=mailshot_pk)

        mailshot.pk = None
        mailshot._state.adding = True
        mailshot.status = Mailshot.Statuses.DRAFT
        mailshot.version += 1
        mailshot.save()

        return redirect(reverse("mailshot-edit", kwargs={"mailshot_pk": mailshot.pk}))


def _check_permission(user: User) -> bool:
    """Check the given user has permission to access mailshot."""

    if user.has_perm(Perms.sys.ilb_admin):
        return True

    importer_access = user.has_perm("web.importer_access")
    exporter_acesss = user.has_perm("web.exporter_access")

    return importer_access or exporter_acesss
