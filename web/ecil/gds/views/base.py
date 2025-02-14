from typing import Any, ClassVar

from django import forms as django_forms
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import FormView

from .types import FormStep
from .utils import (
    delete_session_form_data,
    get_session_form_data,
    get_step_and_field_pairs,
    save_session_form_data,
)


# TODO: Unless refactored this can only work with Model Forms
class MultiStepFormView(FormView):
    form_steps: ClassVar[dict[str, FormStep]]

    @classmethod
    def cache_prefix(cls):
        return cls.__name__

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        if self.steps.index(self.current_step) > 0:
            url = self.get_previous_step_url()
            # TODO: This should use a python serializer from gds.components.serializers
            context["back_link_kwargs"] = {"text": "Back", "href": url}

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

    def get_next_step_url(self) -> str:
        raise NotImplementedError()

    def get_previous_step_url(self) -> str:
        raise NotImplementedError()

    def get_summary_url(self) -> str:
        raise NotImplementedError()


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

    def get_summary_items(self, context: dict[str, Any]) -> dict[str, dict[str, Any]]:
        submit_form = context["form"]
        items = {}

        for step, field in get_step_and_field_pairs(self.edit_view.form_steps):
            items[field] = self.get_summary_item_row(submit_form, step, field)

        return items

    def get_summary_list_kwargs(self, summary_items: dict[str, dict[str, Any]]) -> dict[str, Any]:
        # TODO: This should use a python serializer from gds.components.serializers
        return {"rows": summary_items.values()}

    def get_summary_cards(self, summary_items: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        # TODO: This should use a python serializer from gds.components.serializers
        return []

    def get_summary_item_row(
        self, form: django_forms.Form | django_forms.ModelForm, step: str, field: str
    ) -> dict[str, Any]:
        return {
            "key": {"text": form.fields[field].label},
            "value": {"text": self.get_display_value(field, form[field].initial)},
            "actions": {
                "items": [
                    {
                        "href": self.get_edit_step_url(step),
                        "text": "Change",
                        "visuallyHiddenText": field,
                    }
                ]
            },
        }

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

            error_list.append({"text": field_error})

        # TODO: This should use a python serializer from gds.components.serializers
        context["error_summary_kwargs"] = {
            "titleText": "There is a problem",
            "errorList": error_list,
        }
        return self.render_to_response(context)
