from typing import TYPE_CHECKING, Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_GET, require_POST
from django.views.generic.detail import DetailView, SingleObjectMixin

from web.domains.case.forms import DocumentForm
from web.domains.case.services import reference
from web.domains.file.utils import create_file_model
from web.models import Template, User
from web.permissions import Perms
from web.tasks import send_mailshot_email_task, send_retract_mailshot_email_task
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


#
# Importer / Exporter applicant mailshot views.
#
class ReceivedMailshotsView(ModelFilterView):
    template_name = "web/domains/mailshot/received.html"
    model = Mailshot
    filterset_class = ReceivedMailshotsFilter
    page_title = "Received Mailshots"

    def has_permission(self) -> bool:
        importer_access = self.request.user.has_perm(Perms.sys.importer_access)
        exporter_acesss = self.request.user.has_perm(Perms.sys.exporter_access)

        return importer_access or exporter_acesss

    def get_filterset(self, **kwargs: Any) -> None:
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


class MailshotReceivedDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Mailshot
    pk_url_kwarg = "mailshot_pk"
    template_name = "web/domains/mailshot/view_received.html"

    def has_permission(self) -> bool:
        user: User = self.request.user
        mailshot: Mailshot = self.get_object()

        if mailshot.is_to_importers and user.has_perm(Perms.sys.importer_access):
            return True

        if mailshot.is_to_exporters and user.has_perm(Perms.sys.exporter_access):
            return True

        return False

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["documents"] = self.object.documents.filter(is_active=True)
        context["page_title"] = f"Viewing Mailshot ({self.object.get_reference()})"

        return context


class ClearMailshotFromWorkbasketView(
    LoginRequiredMixin, PermissionRequiredMixin, SingleObjectMixin, View
):
    # View config
    http_method_names = ["post"]

    # SingleObjectMixin config
    model = Mailshot
    pk_url_kwarg = "mailshot_pk"

    def has_permission(self) -> bool:
        user: User = self.request.user
        mailshot: Mailshot = self.get_object()

        if mailshot.is_to_importers and user.has_perm(Perms.sys.importer_access):
            return True

        if mailshot.is_to_exporters and user.has_perm(Perms.sys.exporter_access):
            return True

        return False

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Remove the mailshot from the `request.user` workbasket."""

        mailshot = self.get_object()
        mailshot.cleared_by.add(self.request.user)

        messages.success(
            request, "Mailshot cleared, it can still be viewed in the Search Mailshots page."
        )

        return redirect(reverse("workbasket"))


#
# ILB Admin Mailshot Views
#
class MailshotListView(ModelFilterView):
    template_name = "web/domains/mailshot/list.html"
    model = Mailshot
    filterset_class = MailshotFilter
    permission_required = [Perms.sys.ilb_admin]
    page_title = "Maintain Mailshots"

    # Only set when the page is first loaded.
    default_filters = {"latest_version": ["on"]}

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


class MailshotCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    MAILSHOT_TEMPLATE_CODE = Template.Codes.PUBLISH_MAILSHOT
    permission_required = [Perms.sys.ilb_admin]

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
    # PostActionMixin config
    post_actions = ["save_draft"]

    # ModelUpdateView config
    template_name = "web/domains/mailshot/edit.html"
    form_class = MailshotForm
    model = Mailshot
    permission_required = [Perms.sys.ilb_admin]
    pk_url_kwarg = "mailshot_pk"

    def get_success_url(self) -> str:
        action = self.request.POST.get("action")

        if action and action == "save_draft":
            return reverse("mailshot-edit", kwargs={"mailshot_pk": self.object.pk})

        return reverse("mailshot-list")

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


@require_POST
@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def cancel_mailshot(request: AuthenticatedHttpRequest, *, mailshot_pk: int) -> HttpResponse:
    with transaction.atomic():
        mailshot = get_object_or_404(Mailshot.objects.select_for_update(), pk=mailshot_pk)

        if mailshot.status != Mailshot.Statuses.DRAFT:
            messages.error(request, "Unable to cancel a mailshot that isn't a draft.")
        else:
            mailshot.status = Mailshot.Statuses.CANCELLED
            mailshot.save()
            messages.success(request, "Mailshot cancelled successfully")

    return redirect("mailshot-list")


@require_POST
@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def publish_mailshot(request: AuthenticatedHttpRequest, *, mailshot_pk: int) -> HttpResponse:
    with transaction.atomic():
        mailshot = get_object_or_404(Mailshot.objects.select_for_update(), pk=mailshot_pk)

        if mailshot.status != Mailshot.Statuses.DRAFT:
            messages.error(request, "Unable to publish a mailshot that isn't a draft.")
            return redirect(reverse("mailshot-edit", kwargs={"mailshot_pk": mailshot.pk}))

        else:
            has_documents = mailshot.documents.filter(is_active=True).exists()

            recipients = []
            if mailshot.is_to_importers:
                recipients.append("importers")
            if mailshot.is_to_exporters:
                recipients.append("exporters")
            form = MailshotForm(
                data=model_to_dict(mailshot) | {"recipients": recipients},
                instance=mailshot,
            )

            if not has_documents:
                messages.error(request, "A document must be uploaded before publishing.")

            if form.is_valid():
                with transaction.atomic():
                    mailshot = form.save(commit=False)
                    mailshot.status = Mailshot.Statuses.PUBLISHED
                    mailshot.published_datetime = timezone.now()
                    mailshot.published_by = request.user

                    if not mailshot.reference:
                        mailshot.reference = reference.get_mailshot_reference(
                            request.icms.lock_manager
                        )
                        mailshot.version = models.F("version") + 1

                    mailshot.save()

                    # Reset cleared by as mailshot may be being republished.
                    mailshot.cleared_by.clear()

                mailshot.refresh_from_db()

                if mailshot.is_email:
                    send_mailshot_email_task.delay(mailshot.pk)

                # Finally add the success message before returning the response.
                messages.success(request, f"{mailshot.get_reference()} published successfully")

                return redirect("mailshot-list")
            else:
                messages.error(request, "Please complete form before publishing.")

                return redirect(reverse("mailshot-edit", kwargs={"mailshot_pk": mailshot.pk}))


class MailshotDetailView(MailshotReceivedDetailView):
    template_name = "web/domains/mailshot/view.html"

    def has_permission(self):
        return self.request.user.has_perm(Perms.sys.ilb_admin)


class MailshotRetractView(ModelUpdateView):
    RETRACT_TEMPLATE_CODE = Template.Codes.RETRACT_MAILSHOT
    template_name = "web/domains/mailshot/retract.html"
    form_class = MailshotRetractForm
    model = Mailshot
    success_url = reverse_lazy("mailshot-list")
    cancel_url = success_url
    permission_required = [Perms.sys.ilb_admin]
    pk_url_kwarg = "mailshot_pk"

    def __init__(self, *args, **kwargs):
        template = Template.objects.get(template_code=self.RETRACT_TEMPLATE_CODE)
        self.initial = {
            "retract_email_subject": template.template_title,
            "retract_email_body": template.template_content,
        }

    def handle_notification(self, mailshot):
        if mailshot.is_retraction_email:
            send_retract_mailshot_email_task.delay(mailshot.pk)

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
    has_perm = (
        request.user.has_perm(Perms.sys.ilb_admin)
        or request.user.has_perm(Perms.sys.importer_access)
        or request.user.has_perm(Perms.sys.exporter_access)
    )

    if not has_perm:
        raise PermissionDenied

    mailshot = get_object_or_404(Mailshot, pk=mailshot_pk)
    document = get_object_or_404(mailshot.documents, pk=document_pk)

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
