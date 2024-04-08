from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.forms.models import BaseInlineFormSet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic import View
from django.views.generic.detail import (
    SingleObjectMixin,
    SingleObjectTemplateResponseMixin,
)

from web.types import AuthenticatedHttpRequest


class InlineFormsetView(SingleObjectTemplateResponseMixin, SingleObjectMixin, View):
    """Generic view for inline formsets.

    Notes:
      - Parent model is loaded by SingleObjectMixin and is stored as self.object.
      - Currently restricted to a single formset for simplicity but could be extended to support
        multiple formsets.
      - Formset available in template with context variable 'formset'.
    """

    formset_class: type[BaseInlineFormSet]
    template_name: str
    success_url: str | None
    object: models.Model

    def get(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()

        formset = self.get_formset()

        return self.render_to_response(self.get_context_data(formset=formset))

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()

        formset = self.get_formset()

        if formset.is_valid():
            return self.formset_valid(formset)
        else:
            return self.formset_invalid(formset)

    def get_formset(self) -> BaseInlineFormSet:
        kwargs = self.get_formset_kwargs()
        return self.formset_class(self.request.POST or None, **kwargs)

    def get_formset_kwargs(self) -> dict[str, Any]:
        return {"instance": self.object}

    def formset_valid(self, formset: BaseInlineFormSet) -> HttpResponseRedirect:
        formset.save()
        return redirect(self.get_success_url())

    def formset_invalid(self, formset: BaseInlineFormSet) -> HttpResponse:
        return self.render_to_response(self.get_context_data(formset=formset))

    def get_success_url(self) -> str:
        if not self.success_url:
            raise ImproperlyConfigured("No URL to redirect to. Provide a success_url.")
        return str(self.success_url)  # success_url may be lazy
