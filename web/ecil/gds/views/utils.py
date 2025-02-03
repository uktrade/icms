from collections.abc import Iterator
from typing import Any

from django import forms as django_forms
from django.http import HttpRequest

from .types import FormStep


def get_step_and_field_pairs(form_steps: dict[str, FormStep]) -> Iterator[tuple[str, str]]:
    for step, form_step in form_steps.items():
        for field in form_step.form_cls._meta.fields:
            yield step, field


def save_session_form_data(
    request: HttpRequest, prefix: str, step: str, form: django_forms.Form | django_forms.ModelForm
) -> None:
    # When updating a dict value do this
    # request.session["foo"]["bar"] = 1
    # request.session.modified = True

    for field, value in form.cleaned_data.items():
        # TODO: This will not store all data types
        save_session_value(request, prefix, step, field, value)


def save_session_value(
    request: HttpRequest, prefix: str, step: str, field: str, value: Any
) -> None:
    request.session[f"{prefix}-{step}-{field}"] = value


def get_session_form_data(request: HttpRequest, prefix: str, step: str, field: str) -> Any:
    return request.session.get(f"{prefix}-{step}-{field}", None)


def delete_session_form_data(request: HttpRequest, prefix: str, step: str, field: str) -> None:
    request.session.pop(f"{prefix}-{step}-{field}", None)
