import dataclasses
import re
from collections.abc import Iterator
from typing import TYPE_CHECKING

from web.domains.case.types import ImpOrExp
from web.flow.models import ProcessTypes
from web.models import (
    AccessRequest,
    CertificateOfFreeSaleApplication,
    CFSSchedule,
    Country,
    EndorsementImportApplication,
    ExportApplication,
    ImportApplication,
    Process,
    SILApplication,
    User,
)

from .constants import TemplateCodes
from .context import (
    CoverLetterTemplateContext,
    EmailTemplateContext,
    ScheduleParagraphContext,
)
from .models import CFSScheduleParagraph, Template, TemplateVersion

if TYPE_CHECKING:
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


def find_invalid_placeholders(content: str, valid_placeholders: list[str]) -> list[str]:
    """Return a list of invalid placeholders that appear in the content"""

    return [
        f"[[{placeholder}]]"
        for placeholder in set(re.findall(CONTEXT_VARIABLE_REGEX, content))
        if placeholder not in valid_placeholders
    ]


def replace_template_values(content: str | None, context: "TemplateContextProcessor") -> str:
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


def get_cover_letter_content(application: ImportApplication, document_type: "DocumentTypes") -> str:
    context = CoverLetterTemplateContext(application, document_type)
    return replace_template_values(application.cover_letter_text, context)


def get_email_template_subject_body(
    process: Process,
    template_code: TemplateCodes,
    context_cls: type[EmailTemplateContext] = EmailTemplateContext,
    current_user_name: str = "",
) -> tuple[str, str]:
    template = Template.objects.get(
        template_code=template_code,
        template_type="EMAIL_TEMPLATE",
    )
    context = context_cls(process, current_user_name=current_user_name)
    subject = get_template_title(template, context)
    body = get_template_content(template, context)

    return subject, body


def get_letter_fragment(application: SILApplication) -> str:
    if application.process_type != ProcessTypes.FA_SIL:
        raise ValueError(f"No letter fragments for process type {application.process_type}")

    if application.military_police or application.eu_single_market or application.manufactured:
        return Template.objects.get(
            template_code=Template.Codes.FIREARMS_MARKINGS_NON_STANDARD
        ).template_content

    if (
        application.military_police is False
        and application.eu_single_market is False
        and application.manufactured is False
    ):
        return Template.objects.get(
            template_code=Template.Codes.FIREARMS_MARKINGS_STANDARD
        ).template_content

    raise ValueError("Unable to get letter fragment due to missing application data")


def add_application_cover_letter(application: ImportApplication, template: Template) -> None:
    """Adds a cover letter to an import application"""

    application.cover_letter_text = template.template_content
    application.save()


def add_application_default_cover_letter(application: "ImportApplication") -> None:
    """Adds default cover letters to an import application"""

    match application.process_type:
        case ProcessTypes.FA_DFL:
            template = Template.objects.get(
                template_code=Template.Codes.COVER_FIREARMS_DEACTIVATED_FIREARMS
            )
            add_application_cover_letter(application, template)
        case ProcessTypes.FA_OIL:
            template = Template.objects.get(template_code=Template.Codes.COVER_FIREARMS_OIL)
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


def get_application_update_template_data(application: ImpOrExp) -> tuple[str, str]:
    match application:
        case ImportApplication():
            return get_email_template_subject_body(application, Template.Codes.IMA_APP_UPDATE)
        case ExportApplication():
            return get_email_template_subject_body(
                application, Template.Codes.CA_APPLICATION_UPDATE_EMAIL
            )
        case _:
            raise ValueError(
                "Application must be an instance of ImportApplication / ExportApplication"
            )


def get_fir_template_data(process: Process, current_user: User) -> tuple[str, str]:
    match process:
        case ImportApplication():
            return get_email_template_subject_body(process, Template.Codes.IMA_RFI)
        case ExportApplication():
            return get_email_template_subject_body(process, Template.Codes.CA_RFI_EMAIL)
        case AccessRequest():
            current_user_name = current_user.full_name
            return get_email_template_subject_body(
                process, Template.Codes.IAR_RFI_EMAIL, current_user_name=current_user_name
            )
        case _:
            raise ValueError(
                "Process must be an instance of ImportApplication / ExportApplication / AccessRequest"
            )


@dataclasses.dataclass
class ScheduleParagraphs:
    schedule: CFSSchedule
    template: Template
    header: str = dataclasses.field(init=False)
    introduction: str = dataclasses.field(init=False)
    paragraph: str = dataclasses.field(init=False)
    product: str = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self._ctx = ScheduleParagraphContext(self.schedule, self.template.country_translation_set)
        names = CFSScheduleParagraph.ParagraphName
        self.header = self.content(names.SCHEDULE_HEADER)
        self.introduction = self.content(names.SCHEDULE_INTRODUCTION)
        self.product = self.content(names.PRODUCTS)
        self.paragraph = " ".join(self._get_paragraphs())

    def _get_paragraphs(self) -> Iterator[str]:
        is_ni = self.schedule.application.exporter_office.is_in_northern_ireland
        names = CFSScheduleParagraph.ParagraphName

        if self.schedule.exporter_status == self.schedule.ExporterStatus.IS_MANUFACTURER:
            yield self.content(names.IS_MANUFACTURER)
        else:
            yield self.content(names.IS_NOT_MANUFACTURER)

        if self.schedule.schedule_statements_is_responsible_person:
            if is_ni:
                yield self.content(names.EU_COSMETICS_RESPONSIBLE_PERSON_NI)
            else:
                yield self.content(names.EU_COSMETICS_RESPONSIBLE_PERSON)

        yield self.content(names.LEGISLATION_STATEMENT)

        legislations = ", ".join(
            self.schedule.legislations.order_by("name").values_list("name", flat=True)
        )
        yield legislations + "."

        if self.schedule.product_eligibility == self.schedule.ProductEligibility.SOLD_ON_UK_MARKET:
            yield self.content(names.ELIGIBILITY_ON_SALE)
        elif (
            self.schedule.product_eligibility
            == self.schedule.ProductEligibility.MEET_UK_PRODUCT_SAFETY
        ):
            yield self.content(names.ELIGIBILITY_MAY_BE_SOLD)

        if self.schedule.schedule_statements_accordance_with_standards:
            if is_ni:
                yield self.content(names.GOOD_MANUFACTURING_PRACTICE_NI)
            else:
                yield self.content(names.GOOD_MANUFACTURING_PRACTICE)

        if self.schedule.manufacturer_name and self.schedule.manufacturer_address:
            yield self.content(names.COUNTRY_OF_MAN_STATEMENT_WITH_NAME_AND_ADDRESS)

        elif self.schedule.manufacturer_name:
            yield self.content(names.COUNTRY_OF_MAN_STATEMENT_WITH_NAME)
        else:
            yield self.content(names.COUNTRY_OF_MAN_STATEMENT)

    def content(self, name: str) -> str:
        paragraph = CFSScheduleParagraph.objects.get(name=name, template=self.template)
        return replace_template_values(paragraph.content, self._ctx)


@dataclasses.dataclass
class ScheduleText:
    schedule: CFSSchedule
    country: Country
    english_paragraphs: ScheduleParagraphs = dataclasses.field(init=False)
    translation_paragraphs: ScheduleParagraphs | None = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self.set_english_paragraphs()
        self.set_translation_paragraphs()

    def set_english_paragraphs(self) -> None:
        template = Template.objects.get(is_active=True, template_type=Template.CFS_SCHEDULE)
        self.english_paragraphs = ScheduleParagraphs(self.schedule, template)

    def set_translation_paragraphs(self) -> None:
        try:
            template = Template.objects.get(
                is_active=True,
                template_type=Template.CFS_SCHEDULE_TRANSLATION,
                countries__pk=self.country.pk,
            )
            self.translation_paragraphs = ScheduleParagraphs(self.schedule, template)
        except Template.DoesNotExist:
            self.translation_paragraphs = None


def fetch_schedule_text(
    application: CertificateOfFreeSaleApplication, country: Country
) -> dict[int, ScheduleText]:
    return {
        schedule.pk: ScheduleText(schedule, country) for schedule in application.schedules.all()
    }


def fetch_cfs_declaration_translations(country: Country) -> list[str]:
    templates = TemplateVersion.objects.filter(
        is_active=True,
        template__is_active=True,
        template__template_type=Template.CFS_DECLARATION_TRANSLATION,
        template__countries__pk=country.pk,
        content__isnull=False,
    ).order_by("template_id")

    return list(templates.values_list("content", flat=True))
