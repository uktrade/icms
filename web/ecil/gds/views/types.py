import dataclasses

from django import forms


@dataclasses.dataclass
class FormStep:
    form_cls: type[forms.Form | forms.ModelForm]
    template_name: str | None = None
