from dataclasses import dataclass, field

from django.forms import BaseForm
from django.forms.utils import pretty_name


@dataclass
class FieldError:
    """Errors about a single field in an applicaiton."""

    field_name: str
    messages: list[str]


@dataclass
class PageErrors:
    """Errors belonging to a single page."""

    page_name: str
    errors: list[FieldError] = field(default_factory=list)

    # URL of the page
    url: str | None = None

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def add(self, field_error: FieldError) -> None:
        self.errors.append(field_error)


@dataclass
class ApplicationErrors:
    """All errors of an import/export application."""

    page_errors: list[PageErrors] = field(default_factory=list)

    def has_errors(self) -> bool:
        return any(page.has_errors() for page in self.page_errors)

    def add(self, page_errors: PageErrors) -> None:
        self.page_errors.append(page_errors)

    def add_many(self, page_errors: list[PageErrors]) -> None:
        self.page_errors.extend(page_errors)

    def get_page_errors(self, page_name: str) -> PageErrors | None:
        for p in self.page_errors:
            if p.page_name == page_name:
                return p

        return None


def create_page_errors(form: BaseForm, page_errors: PageErrors) -> None:
    """Convert Django form validation errors to FieldError and add them to the
    given PageErrors."""

    # calling this populates form.errors
    form.is_valid()

    form_errors = form.errors.as_data()

    for field_name, error in form_errors.items():
        if field_name != "__all__":
            field_name_user = form.fields[field_name].label

            if field_name_user is None:
                field_name_user = pretty_name(field_name)
        else:
            field_name_user = "Generic"

        field_error = FieldError(field_name=field_name_user, messages=[x.message for x in error])

        page_errors.add(field_error)
