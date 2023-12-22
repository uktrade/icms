from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DetailView, UpdateView
from django.views.generic.list import ListView

from web.domains.file.utils import create_file_model
from web.models import Signature
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest

from .forms import SignatureForm
from .utils import get_signature_file_base64  # /PS-IGNORE


class SignatureListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "web/domains/signature/list-view.html"
    model = Signature
    ordering = "-created_datetime"
    permission_required = Perms.sys.manage_signatures


class SignatureDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    template_name = "web/domains/signature/view.html"
    permission_required = Perms.sys.manage_signatures
    http_method_names = ["get"]
    model = Signature
    pk_url_kwarg = "signature_pk"
    context_object_name = "object"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context | {"signature_file": get_signature_file_base64(self.object)}


class SignatureMixin:
    request: AuthenticatedHttpRequest

    @staticmethod
    def update_signature(signature: Signature, message: str) -> None:
        """Updates the signature history log and saves the object

        :param signature: the signature object to be updated
        :param message: the log message to be saved in the signature object history
        """

        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        history = f"\n{signature.history}" if signature.history else ""
        signature.history = f"{timestamp} - {message}{history}"
        signature.save()

    def get_active_signature(self) -> None:
        try:
            active_signature = Signature.objects.select_for_update().get(is_active=True)
        except Signature.DoesNotExist:
            active_signature = None

        self.active_signature = active_signature

    def archive_active_signature(self, name: str, created: bool = False) -> str:
        """Archives the active signature to inactive and returns the log message

        :param name: name of the signature to be set active
        :param created: boolean to determine if the signature being set active is newly created
        :return: log message for signature being set active
        """

        if not self.active_signature:
            if created:
                return f'Signature "{name}" added by {self.request.user} and set to the active signature.'

            return f"Set active by {self.request.user}."

        self.active_signature.is_active = False
        self.update_signature(
            self.active_signature,
            f'Archived by {self.request.user}. Replaced by signature "{name}"',
        )

        if created:
            return (
                f'Signature "{name}" added by {self.request.user} and set to the active signature.'
                f' Replaces signature "{self.active_signature.name}"'
            )

        return (
            f'Set active by {self.request.user}. Replaces signature "{self.active_signature.name}"'
        )


class SignatureCreateView(LoginRequiredMixin, PermissionRequiredMixin, SignatureMixin, CreateView):
    template_name = "web/domains/signature/create.html"
    form_class = SignatureForm
    permission_required = Perms.sys.manage_signatures

    def get_initial(self) -> dict[str, Any]:
        return {"signatory": "Import Licensing Branch"}

    def form_valid(self, form):
        with transaction.atomic():
            document = form.cleaned_data["file"]
            set_active = form.cleaned_data.get("is_active")
            name = form.cleaned_data["name"]

            if set_active:
                self.get_active_signature()
                message = self.archive_active_signature(name, True)
            else:
                message = f'Signature "{name}" added by {self.request.user} but is not set to the active signature.'

            extra_args = {
                field: value
                for (field, value) in form.cleaned_data.items()
                if field not in ["file"]
            }

            signature = create_file_model(
                document,
                self.request.user,
                Signature.objects.select_for_update(),
                extra_args=extra_args,
            )
            self.update_signature(signature, message)
            messages.success(self.request, message)

            return redirect(reverse("signature-list"))

    def get_success_url(self):
        return reverse(reverse("signature-list"))


class SignatureSetActiveView(
    LoginRequiredMixin, PermissionRequiredMixin, SignatureMixin, UpdateView
):
    permission_required = Perms.sys.manage_signatures
    http_method_names = ["post"]
    model = Signature
    pk_url_kwarg = "signature_pk"

    def post(
        self, request: AuthenticatedHttpRequest, *args: str, **kwargs: Any
    ) -> AuthenticatedHttpRequest:
        pk = kwargs.get(self.pk_url_kwarg)
        with transaction.atomic():
            # Only one signature can be active, set currently active signatures inactive
            self.get_active_signature()

            if self.active_signature and self.active_signature.pk == pk:
                messages.success(
                    request,
                    f'Signature "{self.active_signature.name}" is already the active signature.',
                )
                return redirect(reverse("signature-list"))

            signature: Signature = get_object_or_404(Signature.objects.select_for_update(), pk=pk)

            message = self.archive_active_signature(signature.name)
            signature.is_active = True
            self.update_signature(signature, message)

            messages.success(
                request, f'Signature "{signature.name}" is set to the active signature.'
            )
            return redirect(reverse("signature-list"))
