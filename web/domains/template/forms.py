from django import forms
from django_filters import CharFilter, ChoiceFilter, FilterSet
from django_select2 import forms as s2forms

from web.domains.template.widgets import EndorsementTemplateWidget

from .models import Template


class GenericTemplate(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_fields(self.instance.template_type)
        self.enable_html_editor(self.instance.template_type)

    def set_fields(self, template_type):
        if template_type == Template.EMAIL_TEMPLATE:
            del self.fields["countries"]
            self.fields["template_title"].label = "Email Subject"
            self.fields["template_content"].label = "Email Body"

        if template_type == Template.LETTER_TEMPLATE:
            del self.fields["countries"]
            del self.fields["template_title"]
            self.fields["template_content"].label = "Letter"

        if template_type == Template.DECLARATION:
            self.fields["template_name"].label = "Declaration Title"
            self.fields["template_content"].label = "Declaration Text"
            self.fields[
                "template_content"
            ].help_text = "This will be displayed as the main text of the Submit page"
            del self.fields["countries"]
            del self.fields["template_title"]

        if template_type == Template.CFS_DECLARATION_TRANSLATION:
            self.fields["template_name"].label = "CFS Translation Name"
            self.fields["template_content"].label = "Translation"
            self.fields[
                "template_content"
            ].help_text = "This will be displayed as the main text of the Submit page"
            del self.fields["template_title"]

        if template_type == Template.ENDORSEMENT:
            self.fields["template_name"].label = "Endorsment Name"
            self.fields["template_content"].label = "Endorsement Text"
            del self.fields["countries"]
            del self.fields["template_title"]

        if template_type == Template.LETTER_FRAGMENT:
            del self.fields["countries"]
            del self.fields["template_title"]
            self.fields["template_name"].label = "Fragment Name"
            self.fields["template_content"].label = "Fragment Text"

    def enable_html_editor(self, template_type):
        """
        Sets lang=html on textarea boxes that need to show an html editor
        """
        if template_type in (Template.LETTER_TEMPLATE, Template.LETTER_FRAGMENT):
            self.fields["template_content"].widget = forms.Textarea(attrs={"lang": "html"})

    class Meta:
        model = Template
        fields = ["template_name", "countries", "template_title", "template_content"]


class EndorsementCreateTemplateForm(GenericTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        del self.fields["template_title"]
        self.fields["template_content"].label = "Endorsement Text"
        self.fields["template_name"].label = "Endorsement Name"


class TemplatesFilter(FilterSet):
    # Fields of the model that can be filtered
    template_name = CharFilter(lookup_expr="icontains", label="Template Name")
    application_domain = ChoiceFilter(
        choices=Template.DOMAINS, lookup_expr="exact", label="Application Domain"
    )
    template_type = ChoiceFilter(choices=Template.TYPES, lookup_expr="exact", label="Template Type")
    template_title = CharFilter(lookup_expr="icontains", label="Template Title")
    template_content = CharFilter(lookup_expr="icontains", label="Template Content")
    is_active = ChoiceFilter(choices=Template.STATUS, lookup_expr="exact", label="Template Status")

    class Meta:
        model = Template
        fields = []  # Django complains without fields set in the meta


class EndorsementUsageForm(forms.Form):
    linked_endorsement = forms.ModelChoiceField(
        label="",
        help_text="""
            Search an endorsement to add. Endorsements returned are matched against
            name and content.
        """,
        queryset=Template.objects.filter(template_type=Template.ENDORSEMENT),
        widget=EndorsementTemplateWidget,
    )


class CFSDeclarationTranslationForm(forms.ModelForm):
    template_name = forms.CharField(label="CFS Translation Name")
    template_content = forms.CharField(label="Translation", widget=forms.Textarea)

    class Meta:
        model = Template
        fields = ("template_name", "countries", "template_content")
        widgets = {
            "countries": s2forms.Select2MultipleWidget,
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.application_domain = Template.CERTIFICATE_APPLICATION
        instance.template_type = Template.CFS_DECLARATION_TRANSLATION
        if commit:
            instance.save()
            self.save_m2m()
        return instance
