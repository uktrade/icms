import structlog as logging
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, reverse
from django.views.generic import FormView, ListView, View

from web.auth.mixins import RequireRegisteredMixin
from web.views.mixins import FileUploadMixin

from . import forms, models

logger = logging.getLogger(__name__)


def _parent_process(request):
    """
        Resolve parent process from url parameter parent_process_pk

        Resolves concrete Process model. E.g. ImporterAccessRequestProcess,
        ExporterAccessRequestProcess, etc
    """
    raise NotImplementedError
    # TODO: fixme
    # kwargs = request.resolver_match.kwargs
    # parent_process_pk = kwargs.get("parent_process_pk")
    # logger.debug(f"Parent process: {parent_process_pk}")
    # base_process = get_object_or_404(Process, pk=parent_process_pk)
    # parent_process = get_object_or_404(base_process.flow_class.process_class, pk=parent_process_pk)
    # # If parent process is finished no new FIR is to be allowed
    # if parent_process.finished:
    #     raise Http404("Parent process not found")
    # return parent_process


def _process(view):
    """
        Resolve FIR process from url parameter process_pk
    """
    return models.FurtherInformationRequestProcess.objects.get(
        pk=view.request.resolver_match.kwargs.get("process_pk")
    )
    return _process


def _check_requester_permission(view):
    """
        Check if user has reqeuster permission
    """
    return view.request.user.has_perm(_process(view).config("requester_permission"))


def _check_responder_permission(view):
    """
        Check if user has reqeuster permission
    """
    return view.request.user.has_perm(_process(view).config("responder_permission"))


def _fir_list_url(parent_process):
    """
        Return url for FIR list page of parent process
    """
    namespace = parent_process.fir_config()["namespace"]
    return reverse(f"{namespace}:fir-list", args=(parent_process.pk,),)


class FurtherInformationRequestListView(RequireRegisteredMixin, ListView):
    """
        List of FIRs for given parent process
    """

    template_name = "web/domains/case/fir/list.html"
    context_object_name = "fir_list"

    def get_queryset(self):
        # Filter by parent process
        parent_process = _parent_process(self.request)
        return parent_process.fir_processes.filter(fir__is_active=True)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["parent_process"] = _parent_process(self.request)
        return context

    def post(self, request, *args, **kwargs):
        if "_withdraw" in request.POST:
            process_id = request.POST.get("_process_id")
            fir_process = self.get_queryset().get(pk=process_id)
            fir_process.withdraw_request()
            return super().get(request, *args, **kwargs)

        return super().post(request, *args, **kwargs)

    def has_permission(self):
        perm_code = _parent_process(self.request).fir_config()["requester_permission"]
        return self.request.user.has_perm(perm_code)

    class Meta:
        model = models.FurtherInformationRequest


class FurtherInformationRequestStartView(RequireRegisteredMixin, FileUploadMixin, FormView):
    """
    Creates a new FIR and associates it with the parent process,
    then display FIR form for new FIR
    """

    template_name = "web/domains/case/fir/start.html"
    form_class = forms.FurtherInformationRequestForm

    def has_permission(self):
        """
            Check parent process for permission
        """
        perm = _parent_process(self.request).fir_config()["requester_permission"]
        return self.request.user.has_perm(perm)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["parent_process"] = _parent_process(self.request)
        return context

    def get_form(self):
        request = self.request
        parent_process = _parent_process(request)
        if request.POST:
            return self.form_class(user=request.user, data=request.POST)

        # initial request
        fir_content = parent_process.fir_content(request)
        return self.form_class(user=request.user, initial=fir_content)

    def _start_process(self, fir):
        """
            Trigger FIR flow start task and return new process intance
        """
        # Lazy import as flows.py imports views.py as well, causing a circular
        # dependency
        from .flows import FurtherInformationRequestFlow

        parent_process = _parent_process(self.request)
        parent_process.on_fir_create(fir)

        # Start a new FIR flow
        return FurtherInformationRequestFlow.start.run(parent_process, fir)

    def form_valid(self, form):
        """
            If the form is valid set parent process and start FIR process
        """
        with transaction.atomic():
            fir = form.save()
            fir.files.set(self.get_files())
            self._start_process(fir)
            return redirect(_fir_list_url(_parent_process(self.request)))


class FutherInformationRequestEditView(RequireRegisteredMixin, FileUploadMixin, View):
    """
        Edit or submit an existing FIR draft
    """

    template_name = "web/domains/case/fir/edit.html"
    form_class = forms.FurtherInformationRequestForm

    def has_permission(self):
        return _check_requester_permission(self)

    def get_file_queryset(self):
        return self.get_form().instance.files

    def get_form(self):
        fir = self.activation.process.fir
        return self.form_class(instance=fir, data=self.request.POST or None)

    def get_success_url(self):
        return _fir_list_url(self.activation.process.parent_process)

    def form_valid(self, form):
        """
            Prevent proceeding with Viewflow if saving as draft
        """
        with transaction.atomic():
            fir = form.save()
            fir.files.set(self.get_files())
            if fir.is_draft():
                return redirect(self.get_success_url())

            return super().form_valid(form)


class FurtherInformationRequestResponseView(
    RequireRegisteredMixin, FileUploadMixin, View
):
    template_name = "web/domains/case/fir/respond.html"
    form_class = forms.FurtherInformationRequestResponseForm

    def has_permission(self):
        return _check_responder_permission(self)

    def get_form(self):
        return self.form_class(
            self.request.user, instance=self.activation.process.fir, data=self.request.POST or None,
        )

    def get_success_url(self):
        return reverse("workbasket")

    def get_file_queryset(self):
        return self.get_form().instance.files

    def form_valid(self, form):
        with transaction.atomic():
            fir = form.save()
            fir.files.set(self.get_files())
            return super().form_valid(form)


class FurtherInformationRequestReviewView(
    RequireRegisteredMixin, FileUploadMixin, View
):
    template_name = "web/domains/case/fir/review.html"

    def has_permission(self):
        return _check_requester_permission(self)

    def form_valid(self, form):
        with transaction.atomic():
            fir = form.instance.fir
            fir.close(self.request.user)
            fir.files.set(self.get_files())
            return super().form_valid(form)

    def get_file_queryset(self):
        return self.get_form().instance.fir.files

    def get_success_url(self):
        return _fir_list_url(self.activation.process.parent_process)
