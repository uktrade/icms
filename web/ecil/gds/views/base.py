import logging
from typing import Any, ClassVar
from urllib import parse

from django import forms as django_forms
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.urls import Resolver404, ResolverMatch, resolve
from django.views.generic import FormView, UpdateView
from pydantic import BaseModel, ConfigDict, ValidationError

from web.ecil.gds import component_serializers as serializers
from web.ecil.gds.utils import get_html_or_text
from web.types import AuthenticatedHttpRequest

from .types import FormStep
from .utils import (
    delete_session_form_data,
    get_session_form_data,
    get_step_and_field_pairs,
    save_session_form_data,
)

logger = logging.getLogger(__name__)


class BackLinkMixin:
    """Adds back_link_kwargs variable to template context.

    Also stores HTTP_REFERER as a session variable to allow back links for views that are
    referenced by several other views.
    """

    from_summary: bool = False

    class QueryParams(BaseModel):
        """Available query params used in this mixin"""

        model_config = ConfigDict(extra="ignore")
        from_summary: bool

    def get(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            params = self.QueryParams.model_validate(request.GET.dict())
            self.from_summary = params.from_summary

        except ValidationError:
            self.from_summary = False

        # Store the referrer url to create the return link later
        referrer = self.request.META.get("HTTP_REFERER", "")  # type: ignore[attr-defined]
        referrer_path: str = parse.urlparse(referrer).path

        try:
            resolver_match: ResolverMatch = resolve(referrer_path)
            self.request.session["_referrer_view"] = resolver_match.view_name  # type: ignore[attr-defined]

        except Resolver404:
            logger.warning("Unable to resolve referrer '%s'", referrer_path)
            pass

        return super().get(request, *args, **kwargs)  # type: ignore[misc]

    def get_referrer_view(self) -> str:
        return self.request.session.get("_referrer_view", "")  # type: ignore[attr-defined]

    def get_context_data(self, **kwargs):
        context: dict[str, Any] = super().get_context_data(**kwargs)  # type: ignore[misc]

        if back_link_url := self.get_back_link_url():
            context["back_link_kwargs"] = serializers.back_link.BackLinkKwargs(
                text="Back", href=back_link_url
            ).model_dump(exclude_defaults=True)
        else:
            context["back_link_kwargs"] = None

        return context

    def get_back_link_url(self) -> str | None:
        raise NotImplementedError()


# TODO: ECIL-697 Remove and replace with ECILUserAccessRequest
class MultiStepFormView(FormView):
    form_steps: ClassVar[dict[str, FormStep]]

    @classmethod
    def cache_prefix(cls):
        return cls.__name__

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        if self.steps.index(self.current_step) > 0:
            url = self.get_previous_step_url()
            context["back_link_kwargs"] = serializers.back_link.BackLinkKwargs(
                text="Back", href=url
            ).model_dump(exclude_defaults=True)

        return context

    def get_form_class(self) -> type[django_forms.Form | django_forms.ModelForm]:
        return self.form_steps[self.current_step].form_cls

    def get_initial(self) -> dict[str, Any]:
        initial = super().get_initial()

        step = self.current_step
        form_step = self.form_steps[self.current_step]

        for f in form_step.form_cls._meta.fields:
            session_value = get_session_form_data(self.request, self.cache_prefix(), step, f)

            if session_value:
                initial[f] = session_value

        return initial

    def form_valid(self, form: django_forms.Form | django_forms.ModelForm) -> HttpResponseRedirect:
        save_session_form_data(self.request, self.cache_prefix(), self.current_step, form)

        return super().form_valid(form)

    def get_success_url(self) -> str:
        if self.next_step == "summary":
            return self.get_summary_url()

        return self.get_next_step_url()

    @property
    def current_step(self) -> str:
        return self.kwargs["step"]

    @property
    def steps(self) -> list[str]:
        return list(self.form_steps.keys())

    @property
    def next_step(self) -> str:
        idx = self.steps.index(self.current_step)
        try:
            next_step = self.steps[idx + 1]
        except IndexError:
            next_step = "summary"

        return next_step

    @property
    def previous_step(self) -> str:
        idx = self.steps.index(self.current_step)
        try:
            prev_step = self.steps[idx - 1]
        except IndexError:
            prev_step = self.steps[0]

        return prev_step

    def get_template_names(self):
        if template := self.form_steps[self.current_step].template_name:
            return [template]

        return super().get_template_names()

    def get_current_step_url(self) -> str:
        raise NotImplementedError()

    def get_next_step_url(self) -> str:
        raise NotImplementedError()

    def get_previous_step_url(self) -> str:
        raise NotImplementedError()

    def get_summary_url(self) -> str:
        raise NotImplementedError()


# TODO: ECIL-697 Remove and replace with ECILUserAccessRequest using SummaryUpdateView
class MultiStepFormSummaryView(FormView):
    edit_view: ClassVar[type[MultiStepFormView]]

    def get_initial(self) -> dict[str, Any]:
        initial = super().get_initial()

        for step, f in get_step_and_field_pairs(self.edit_view.form_steps):
            initial[f] = get_session_form_data(self.request, self.edit_view.cache_prefix(), step, f)

        return initial

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()

        if self.request.method == "POST":
            # Pass in session data as form data when posting the summary view.
            kwargs["data"] = self.get_initial()

        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        summary_items = self.get_summary_items(context)
        summary_list_kwargs = self.get_summary_list_kwargs(summary_items)
        summary_cards = self.get_summary_cards(summary_items)

        return context | {
            "summary_list_kwargs": summary_list_kwargs,
            "summary_cards": summary_cards,
        }

    def get_summary_items(self, context: dict[str, Any]) -> dict[str, serializers.summary_list.Row]:
        submit_form = context["form"]
        items = {}

        for step, field in get_step_and_field_pairs(self.edit_view.form_steps):
            items[field] = self.get_summary_item_row(submit_form, step, field)

        return items

    def get_summary_list_kwargs(
        self, summary_items: dict[str, serializers.summary_list.Row]
    ) -> dict[str, Any]:
        return serializers.summary_list.SummaryListKwargs(
            rows=list(summary_items.values()),
        ).model_dump(exclude_defaults=True)

    def get_summary_cards(
        self, summary_items: dict[str, serializers.summary_list.Row]
    ) -> list[dict[str, Any]]:
        return []

    def get_summary_item_row(
        self, form: django_forms.Form | django_forms.ModelForm, step: str, field: str
    ) -> serializers.summary_list.Row:

        value = self.get_display_value(field, form[field].initial)

        # TODO: Revisit in ECIL-618 to fix missing & optional fields
        if value is None or value == "":
            value = "No value entered (Fix in ECIL-618)"

        row_value_kwargs = get_html_or_text(value)

        return serializers.summary_list.Row(
            key=serializers.summary_list.RowKey(text=form.fields[field].label),
            value=serializers.summary_list.RowValue(**row_value_kwargs),
            actions=serializers.summary_list.RowActions(
                items=[
                    serializers.summary_list.RowActionItem(
                        href=self.get_edit_step_url(step),
                        text="Change",
                        visuallyHiddenText=field,
                    )
                ]
            ),
        )

    def form_valid(self, form: django_forms.Form | django_forms.ModelForm) -> HttpResponseRedirect:
        # Create but don't save record instance
        self.new_object = form.save(commit=False)

        # Allow subclass to modify record
        self.form_valid_save_hook()

        # Save the record (note subclass may have already saved it)
        self.new_object.save()

        # Side effect of using commit=False with model forms is m2m are not saved until
        # the instance has been saved.
        form.save_m2m()

        self.remove_session_data()

        return super().form_valid(form)

    def form_valid_save_hook(self) -> None:
        """Override to do any additional saving to the form model instance."""
        pass

    def remove_session_data(self):
        for step, f in get_step_and_field_pairs(self.edit_view.form_steps):
            delete_session_form_data(self.request, self.edit_view.cache_prefix(), step, f)

    def get_display_value(self, field: str, value: Any) -> str:
        """Default method to display values in summary view."""

        match value:
            case True | "True":
                return "Yes"
            case False | "False":
                return "No"
            case None:
                return ""
            case _:
                return value

    def get_edit_step_url(self, step: str) -> str:
        raise NotImplementedError()

    def form_invalid(self, form: django_forms.Form | django_forms.ModelForm) -> HttpResponse:
        context = self.get_context_data(form=form)
        error_list = []
        for field_name, error in form.errors.items():
            field = form.fields[field_name]
            field_error = f"{field.label}: {','.join(error)}"

            error_list.append(serializers.error_summary.Error(text=field_error))

        context["error_summary_kwargs"] = serializers.error_summary.ErrorSummaryKwargs(
            titleText="There is a problem",
            errorList=error_list,
        ).model_dump(exclude_defaults=True)

        return self.render_to_response(context)


class SummaryUpdateView(UpdateView):
    # UpdateView config
    template_name = "ecil/gds_summary_list.html"
    http_method_names = ["get", "post"]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.request.method == "POST":
            # Pass in object data as form data when posting the summary view.
            kwargs["data"] = model_to_dict(self.object)

        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        summary_items = self.get_summary_items(context)
        summary_list_kwargs = self.get_summary_list_kwargs(summary_items)
        summary_cards = self.get_summary_cards(summary_items)

        return context | {
            "summary_list_kwargs": summary_list_kwargs,
            "summary_cards": summary_cards,
        }

    def get_summary_items(self, context: dict[str, Any]) -> dict[str, serializers.summary_list.Row]:
        raise NotImplementedError()

    def get_summary_item_row(
        self, field: str, key: str, value: str, edit_link: str
    ) -> serializers.summary_list.Row:
        # TODO: Revisit in ECIL-618 to fix missing & optional fields
        if value is None or value == "":
            value = "No value entered (Fix in ECIL-618)"

        row_value_kwargs = get_html_or_text(value)

        qd = QueryDict(mutable=True)
        qd.update({"from_summary": "true"})

        return serializers.summary_list.Row(
            key=serializers.summary_list.RowKey(text=key),
            value=serializers.summary_list.RowValue(**row_value_kwargs),
            actions=serializers.summary_list.RowActions(
                items=[
                    serializers.summary_list.RowActionItem(
                        href=edit_link + f"?{qd.urlencode()}",
                        text="Change",
                        visuallyHiddenText=field,
                    )
                ]
            ),
        )

    def get_summary_list_kwargs(
        self, summary_items: dict[str, serializers.summary_list.Row]
    ) -> dict[str, Any]:
        return serializers.summary_list.SummaryListKwargs(
            rows=list(summary_items.values()),
        ).model_dump(exclude_defaults=True)

    def get_summary_cards(
        self, summary_items: dict[str, serializers.summary_list.Row]
    ) -> list[dict[str, Any]]:
        return []

    def form_invalid(self, form: django_forms.ModelForm) -> HttpResponse:
        context = self.get_context_data(form=form)
        error_list = []
        for field_name, error in form.errors.items():
            field = form.fields[field_name]
            field_error = f"{field.label}: {','.join(error)}"

            error_list.append(serializers.error_summary.Error(text=field_error))

        context["error_summary_kwargs"] = serializers.error_summary.ErrorSummaryKwargs(
            titleText="There is a problem",
            errorList=error_list,
        ).model_dump(exclude_defaults=True)

        return self.render_to_response(context)
