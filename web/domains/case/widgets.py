from django.forms.widgets import CheckboxSelectMultiple


class CaseEmailAttachmentWidgetBase(CheckboxSelectMultiple):
    option_template_name = "django/forms/widgets/input.html"

    def __init__(self, *args, qs, process, file_metadata, **kwargs):
        super().__init__(*args, **kwargs)
        self.qs = qs
        self.process = process
        self.file_metadata = file_metadata

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        # Requires qs to be set on the form
        context["qs"] = self.qs
        context["process"] = self.process
        context["file_metadata"] = self.file_metadata

        return context


class CaseEmailAttachmentsWidget(CaseEmailAttachmentWidgetBase):
    """Widget used to show attachments linked to a case email."""

    template_name = "forms/widgets/case-email-attachments-table.html"


class FirearmsApplicationCaseEmailAttachmentsWidget(CaseEmailAttachmentWidgetBase):
    """Widget used to show attachments linked to a constabulary case email."""

    template_name = "forms/widgets/case-email-firearms-attachments-table.html"
