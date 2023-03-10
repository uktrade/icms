import re
from typing import TYPE_CHECKING

from web.domains.case._import.models import EndorsementImportApplication
from web.flow.models import ProcessTypes

from .context import CoverLetterTemplateContext
from .models import Template

if TYPE_CHECKING:
    from web.domains.case._import.fa_sil.models import SILApplication
    from web.domains.case._import.models import ImportApplication
    from web.types import DocumentTypes

    from .context import TemplateContextProcessor


# e.g. [[CONTACT_NAME]]
TEMPLATE_CONTENT_REGEX = r"\[\[{}]]"
CONTEXT_VARIABLE_REGEX = re.compile(
    r"""
        \[\[        # Opening braces
        ([a-z_]+)   # Match group of a-z and underscore
        ]]          # Closing braces
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)


def add_endorsements_from_application_type(application: "ImportApplication") -> None:
    """Adds active endorsements to application based on application type"""

    if application.endorsements.exists():
        # If there are already endorsements on the application, do not add default endorsements
        return

    endorsements = application.application_type.endorsements.filter(is_active=True)

    EndorsementImportApplication.objects.bulk_create(
        [
            EndorsementImportApplication(
                import_application_id=application.pk,
                content=endorsement.template_content,
            )
            for endorsement in endorsements
        ]
    )


def get_context_dict(content: str, context: "TemplateContextProcessor") -> dict[str, str]:
    return {hit: context[hit] for hit in set(re.findall(CONTEXT_VARIABLE_REGEX, content))}


def replace_template_values(content: str, context: "TemplateContextProcessor") -> str:
    """Returns the template content with the placeholders replaced with their value

    Calling this function with replacements={'foo': 'bar'} will return the template content
    with all occurences of [[foo]] replaced with bar"""

    if content is None:
        return ""

    for replacement, value in get_context_dict(content, context).items():
        content = re.sub(TEMPLATE_CONTENT_REGEX.format(replacement), value, content)

    return content


def get_template_title(template: Template, context: "TemplateContextProcessor") -> str:
    """Gets the title of a template with replacements for placeholder values"""
    return replace_template_values(template.template_title, context)


def get_template_content(template: Template, context: "TemplateContextProcessor") -> str:
    """Gets the content of a template with replacements for placeholder values"""
    return replace_template_values(template.template_content, context)


def get_cover_letter_content(
    application: "ImportApplication", document_type: "DocumentTypes"
) -> str:
    context = CoverLetterTemplateContext(application, document_type)
    return replace_template_values(application.cover_letter_text, context)


def get_letter_fragment(application: "SILApplication") -> str:
    if application.process_type != ProcessTypes.FA_SIL:
        raise ValueError(f"No letter fragments for process type {application.process_type}")

    if application.military_police or application.eu_single_market or application.manufactured:
        return Template.objects.get(template_code="FIREARMS_MARKINGS_NON_STANDARD").template_content

    if (
        application.military_police is False
        and application.eu_single_market is False
        and application.manufactured is False
    ):
        return Template.objects.get(template_code="FIREARMS_MARKINGS_STANDARD").template_content

    raise ValueError("Unable to get letter fragment due to missing application data")


def add_application_cover_letter(application: "ImportApplication", template: Template) -> None:
    """Adds a cover letter to an import application"""

    application.cover_letter_text = template.template_content
    application.save()


def add_application_default_cover_letter(application: "ImportApplication") -> None:
    """Adds default cover letters to an import application"""

    match application.process_type:
        case ProcessTypes.FA_DFL:
            template = Template.objects.get(template_code="COVER_FIREARMS_DEACTIVATED_FIREARMS")
            add_application_cover_letter(application, template)
        case ProcessTypes.FA_OIL:
            template = Template.objects.get(template_code="COVER_FIREARMS_OIL")
            add_application_cover_letter(application, template)
        case ProcessTypes.FA_SIL:
            # SIL applcation cover letters are added manually
            pass
        case _:
            raise ValueError(f"No default cover letter for {application.process_type}")


def add_template_data_on_submit(application: "ImportApplication") -> None:
    """Adds data required for applications response preparation on submit"""

    add_endorsements_from_application_type(application)

    if application.application_type.cover_letter_flag:
        add_application_default_cover_letter(application)
