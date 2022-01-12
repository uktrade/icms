import structlog as logging
from django.forms import Form

logger = logging.getLogger(__name__)


class ReadonlyFormMixin(Form):
    """Makes forms read only, prevents changing any data"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self.fields.keys():
            self.fields[key].disabled = True

    def save(self, *args, **kwargs):
        pass


class OptionalFormMixin:
    """Makes all form fields optional to allow partial saving."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # type: ignore[call-arg]

        for f in self.fields:  # type: ignore[attr-defined]
            self.fields[f].required = False  # type: ignore[attr-defined]
